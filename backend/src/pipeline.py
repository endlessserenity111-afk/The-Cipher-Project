from pathlib import Path
import json
import time
import numpy as np
import pandas as pd

from config import *
from .io_utils import ensure_dirs, read_csv, write_csv, snapshot_files
from .cleaning import basic_cleaning, build_quality_report, build_dataset_summary
from .entity_normalization import normalize_entities
from .matching import match_records
from .feature_engineering import build_project_features, add_peer_features
from .expenditure_checks import build_mp_indicators
from .anomaly_detection import add_statistical_anomalies, add_isolation_forest
from .risk_scoring import score_projects, score_mp_indicators
from .aggregations import state_rollup, category_rollup, constituency_rollup
from .validation import validate_projects, validate_matches, validate_outputs
from .match_review import build_review_samples


def standardize_recommendations(df):
    x=df.rename(columns={
        "Work ID":"work_id","Work Description":"work_description","Category":"category","MP Name":"mp_name",
        "Constituency":"constituency","State":"state","House":"house","Recommended Amount (₹)":"recommended_amount",
        "Recommendation Date":"recommendation_date","IDA":"ida",
    }).copy()
    x=basic_cleaning(x,["recommended_amount"],["recommendation_date"],["work_description","category","mp_name","constituency","state","house","ida","work_id"])
    e=normalize_entities(x.rename(columns={"mp_name":"MP Name","constituency":"Constituency","state":"State","house":"House","ida":"IDA","category":"Category","work_description":"Work Description","work_id":"Work ID"}))
    e["mp_name"]=x["mp_name"]; e["constituency"]=x["constituency"]; e["state"]=x["state"]; e["house"]=x["house"]; e["ida"]=x["ida"]; e["category"]=x["category"]; e["work_description"]=x["work_description"]; e["work_id"]=x["work_id"]
    e["work_id_key"]=e["work_id_norm_key"] if "work_id_norm_key" in e else e.get("work_id_key", pd.Series("", index=e.index))
    return e


def standardize_completions(df):
    x=df.rename(columns={
        "Work ID":"work_id","Work Description":"work_description","Category":"category","MP Name":"mp_name",
        "Constituency":"constituency","State":"state","House":"house","Final Amount (₹)":"final_amount",
        "Completed Date":"completed_date","IDA":"ida",
    }).copy()
    x=basic_cleaning(x,["final_amount"],["completed_date"],["work_description","category","mp_name","constituency","state","house","ida","work_id"])
    e=normalize_entities(x.rename(columns={"mp_name":"MP Name","constituency":"Constituency","state":"State","house":"House","ida":"IDA","category":"Category","work_description":"Work Description","work_id":"Work ID"}))
    e["mp_name"]=x["mp_name"]; e["constituency"]=x["constituency"]; e["state"]=x["state"]; e["house"]=x["house"]; e["ida"]=x["ida"]; e["category"]=x["category"]; e["work_description"]=x["work_description"]; e["work_id"]=x["work_id"]
    e["work_id_key"]=e["work_id_norm_key"] if "work_id_norm_key" in e else e.get("work_id_key", pd.Series("", index=e.index))
    return e


def standardize_expenditures(df):
    x=df.rename(columns={
        "MP Name":"mp_name","Constituency":"constituency","State":"state","House":"house","Work Description":"work_description",
        "Vendor":"vendor_name","IDA":"ida","Expenditure Amount (₹)":"amount_paid","Expenditure Date":"expenditure_date","Payment Status":"payment_status",
    }).copy()
    x=basic_cleaning(x,["amount_paid"],["expenditure_date"],["work_description","mp_name","constituency","state","house","vendor_name","ida","payment_status"])
    e=normalize_entities(x.rename(columns={"mp_name":"MP Name","constituency":"Constituency","state":"State","house":"House","ida":"IDA","vendor_name":"Vendor","work_description":"Work Description"}))
    e["mp_name"]=x["mp_name"]; e["constituency"]=x["constituency"]; e["state"]=x["state"]; e["house"]=x["house"]; e["ida"]=x["ida"]; e["vendor_name"]=x["vendor_name"]; e["work_description"]=x["work_description"]
    e["total_expenditure"]=np.nan if False else 0
    return e


def standardize_mp_summary(df):
    x=df.rename(columns={
        "MP Name":"mp_name","Constituency":"constituency","State":"state","House":"house",
        "Allocated Amount (₹)":"allocated_amount","Total Expenditure (₹)":"total_expenditure","Unspent Amount (₹)":"unspent_amount",
        "Utilization %":"utilization_pct","Completed Works":"completed_works","Recommended Works":"recommended_works",
        "Completion Rate %":"completion_rate_pct","Transaction Count":"transaction_count","Successful Payments":"successful_payments","Pending Payments":"pending_payments",
    }).copy()
    x=basic_cleaning(x,["allocated_amount","total_expenditure","unspent_amount"],[],["mp_name","constituency","state","house"])
    return x


def run_pipeline(limit=None):
    started=time.time()
    ensure_dirs(RAW_DIR,PROCESSED_DIR,OUTPUT_DIR,REVIEW_DIR)
    required=[RECOMMENDED_FILE,COMPLETED_FILE,EXPENDITURE_FILE,MP_SUMMARY_FILE]
    missing=[str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required input files: " + ", ".join(missing))

    rec_raw=read_csv(RECOMMENDED_FILE)
    comp_raw=read_csv(COMPLETED_FILE)
    exp_raw=read_csv(EXPENDITURE_FILE)
    sum_raw=read_csv(MP_SUMMARY_FILE)
    if limit is not None:
        if limit <= 0:
            raise ValueError("--limit must be a positive integer")
        rec_raw=rec_raw.head(limit).copy()

    rec=standardize_recommendations(rec_raw)
    comp=standardize_completions(comp_raw)
    exp=standardize_expenditures(exp_raw)
    summary=standardize_mp_summary(sum_raw)

    write_csv(build_dataset_summary({"recommendations":rec,"completions":comp,"expenditures":exp,"mp_summary":summary}),OUTPUT_DIR/"dataset_summary.csv")
    write_csv(build_quality_report({"recommendations":rec,"completions":comp,"expenditures":exp,"mp_summary":summary}),OUTPUT_DIR/"data_quality_report.csv")

    matches=match_records(rec,comp)
    write_csv(matches,OUTPUT_DIR/"match_results.csv")
    write_csv(validate_matches(matches),OUTPUT_DIR/"match_validation.csv")
    review=build_review_samples(matches,rec,comp,REVIEW_DIR)

    projects=build_project_features(rec,comp,matches)
    if projects.empty:
        raise RuntimeError("No project matches passed the minimum matching threshold. Check match_results.csv.")
    projects=add_peer_features(projects)
    projects=add_statistical_anomalies(projects)
    projects=add_isolation_forest(projects)
    projects=score_projects(projects)
    write_csv(projects,OUTPUT_DIR/"project_risk_scores.csv")
    write_csv(projects[projects["risk_level"]=="HIGH"],OUTPUT_DIR/"high_risk_projects.csv")

    mp=build_mp_indicators(exp,comp,summary)
    mp=score_mp_indicators(mp)
    write_csv(mp,OUTPUT_DIR/"mp_risk_indicators.csv")

    write_csv(state_rollup(projects),OUTPUT_DIR/"state_rollup.csv")
    write_csv(category_rollup(projects),OUTPUT_DIR/"category_rollup.csv")
    write_csv(constituency_rollup(projects),OUTPUT_DIR/"constituency_rollup.csv")

    write_csv(validate_projects(projects),OUTPUT_DIR/"project_validation.csv")
    write_csv(validate_outputs(projects,mp),OUTPUT_DIR/"output_validation.csv")

    summary_obj={
        "mode":"limited" if limit is not None else "full",
        "limit":int(limit) if limit is not None else None,
        "runtime_seconds":round(time.time()-started,2),
        "recommendations":int(len(rec)),"completed_works":int(len(comp)),"expenditures":int(len(exp)),"mp_summary_rows":int(len(summary)),
        "tier1_matches":int((matches["match_tier"]=="Tier 1").sum()),"tier2_matches":int((matches["match_tier"]=="Tier 2").sum()),"unmatched":int((matches["match_tier"]=="Unmatched").sum()),
        "high_risk_projects":int((projects["risk_level"]=="HIGH").sum()),"medium_risk_projects":int((projects["risk_level"]=="MEDIUM").sum()),"low_risk_projects":int((projects["risk_level"]=="LOW").sum()),
        "ml_anomaly_projects":int(projects["ml_anomaly_flag"].sum()),
        "review":review,
        "risk_note":"Risk scores are analytical assessments, not fraud probabilities or findings.",
        "expenditure_note":"Expenditure indicators are aggregated at MP/constituency/IDA level because expenditure records do not contain a reliable Work ID.",
    }
    manifest={
        "inputs":snapshot_files(required),
        "configuration":{
            "TIER1_THRESHOLD":TIER1_THRESHOLD,"TIER2_THRESHOLD":TIER2_THRESHOLD,"MAX_CANDIDATES_PER_REC":MAX_CANDIDATES_PER_REC,
            "DATE_WINDOW_DAYS":DATE_WINDOW_DAYS,"RANDOM_STATE":RANDOM_STATE,
        },
        "run":summary_obj,
    }
    (OUTPUT_DIR/"pipeline_summary.json").write_text(json.dumps(summary_obj,indent=2),encoding="utf-8")
    (OUTPUT_DIR/"pipeline_manifest.json").write_text(json.dumps(manifest,indent=2,default=str),encoding="utf-8")
    return summary_obj
