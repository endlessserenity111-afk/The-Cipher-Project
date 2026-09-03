from pathlib import Path
import json
import pandas as pd

from config import *
from .io_utils import ensure_dirs, read_csv, write_csv
from .cleaning import basic_cleaning, add_normalized_columns, build_quality_report
from .entity_normalization import normalize_entities, add_canonical_entities
from .matching import match_records
from .feature_engineering import build_project_features
from .expenditure_checks import build_mp_indicators
from .anomaly_detection import add_statistical_anomalies, add_isolation_forest
from .risk_scoring import score_projects, score_mp_indicators
from .aggregations import state_rollup, category_rollup, district_rollup
from .validation import validate_projects, validate_matches


def standardize_recommendations(df):
    x = df.rename(columns={
        "Work ID":"work_id", "Work Description":"work_description", "Category":"category",
        "MP Name":"mp_name", "Constituency":"constituency", "State":"state", "House":"house",
        "Recommended Amount (₹)":"recommended_amount", "Recommendation Date":"recommendation_date", "IDA":"ida"
    }).copy()
    x = basic_cleaning(x, ["recommended_amount"], ["recommendation_date"], ["work_description","category","mp_name","constituency","state","house","ida"])
    x = normalize_entities(x.rename(columns={"mp_name":"MP Name","constituency":"Constituency","state":"State","house":"House","ida":"IDA","category":"Category","work_description":"Work Description"}))
    x = x.rename(columns={"MP Name":"mp_name_raw","Constituency":"constituency_raw","State":"state_raw","House":"house_raw","IDA":"ida_raw","Category":"category_raw","Work Description":"work_description_raw"})
    # normalized columns are present but the canonical raw analytical names remain clean.
    x["mp_name"] = x["mp_name_raw"]; x["constituency"] = x["constituency_raw"]; x["state"] = x["state_raw"]; x["house"] = x["house_raw"]; x["ida"] = x["ida_raw"]; x["category"] = x["category_raw"]; x["work_description"] = x["work_description_raw"]
    return add_canonical_entities(x)


def standardize_completions(df):
    x = df.rename(columns={
        "Work ID":"work_id", "Work Description":"work_description", "Category":"category",
        "MP Name":"mp_name", "Constituency":"constituency", "State":"state", "House":"house",
        "Final Amount (₹)":"final_amount", "Completed Date":"completed_date", "IDA":"ida"
    }).copy()
    x = basic_cleaning(x, ["final_amount"], ["completed_date"], ["work_description","category","mp_name","constituency","state","house","ida"])
    x = normalize_entities(x.rename(columns={"mp_name":"MP Name","constituency":"Constituency","state":"State","house":"House","ida":"IDA","category":"Category","work_description":"Work Description"}))
    x = x.rename(columns={"MP Name":"mp_name_raw","Constituency":"constituency_raw","State":"state_raw","House":"house_raw","IDA":"ida_raw","Category":"category_raw","Work Description":"work_description_raw"})
    x["mp_name"] = x["mp_name_raw"]; x["constituency"] = x["constituency_raw"]; x["state"] = x["state_raw"]; x["house"] = x["house_raw"]; x["ida"] = x["ida_raw"]; x["category"] = x["category_raw"]; x["work_description"] = x["work_description_raw"]
    return add_canonical_entities(x)


def standardize_expenditures(df):
    x = df.rename(columns={
        "MP Name":"mp_name", "Constituency":"constituency", "State":"state", "House":"house",
        "Work Description":"work_description", "Vendor":"vendor_name", "IDA":"ida",
        "Expenditure Amount (₹)":"amount_paid", "Expenditure Date":"expenditure_date", "Payment Status":"payment_status"
    }).copy()
    x = basic_cleaning(x, ["amount_paid"], ["expenditure_date"], ["work_description","mp_name","constituency","state","house","vendor_name","ida","payment_status"])
    x = normalize_entities(x.rename(columns={"mp_name":"MP Name","constituency":"Constituency","state":"State","house":"House","ida":"IDA","vendor_name":"Vendor","work_description":"Work Description"}))
    return x.rename(columns={"MP Name":"mp_name_raw","Constituency":"constituency_raw","State":"state_raw","House":"house_raw","IDA":"ida_raw","Vendor":"vendor_name_raw","Work Description":"work_description_raw"}).assign(
        mp_name=lambda d:d["mp_name_raw"], constituency=lambda d:d["constituency_raw"], state=lambda d:d["state_raw"], house=lambda d:d["house_raw"], ida=lambda d:d["ida_raw"], vendor_name=lambda d:d["vendor_name_raw"], work_description=lambda d:d["work_description_raw"]
    )


def standardize_mp_summary(df):
    return basic_cleaning(df, ["Allocated Amount (₹)","Total Expenditure (₹)","Unspent Amount (₹)"], [], ["MP Name","Constituency","State","House"])


def run_pipeline() -> dict:
    ensure_dirs(RAW_DIR, PROCESSED_DIR, OUTPUT_DIR)
    rec_raw = read_csv(RECOMMENDED_FILE)
    comp_raw = read_csv(COMPLETED_FILE)
    exp_raw = read_csv(EXPENDITURE_FILE)
    sum_raw = read_csv(MP_SUMMARY_FILE)

    rec = standardize_recommendations(rec_raw)
    comp = standardize_completions(comp_raw)
    exp = standardize_expenditures(exp_raw)
    summary = standardize_mp_summary(sum_raw)

    quality = build_quality_report({"recommendations":rec,"completions":comp,"expenditures":exp,"mp_summary":summary})
    write_csv(quality, OUTPUT_DIR / "data_quality_report.csv")

    matches = match_records(rec, comp)
    write_csv(matches, OUTPUT_DIR / "match_results.csv")
    match_validation = validate_matches(matches)
    write_csv(match_validation, OUTPUT_DIR / "match_validation.csv")

    projects = build_project_features(rec, comp, matches)
    if projects.empty:
        raise RuntimeError("No matches passed the minimum matching threshold; inspect match_results.csv")
    projects = add_statistical_anomalies(projects)
    projects = add_isolation_forest(projects)
    projects = score_projects(projects)
    write_csv(projects, OUTPUT_DIR / "project_risk_scores.csv")
    write_csv(projects[projects["risk_level"]=="HIGH"], OUTPUT_DIR / "high_risk_projects.csv")

    mp = build_mp_indicators(exp, projects)
    mp = score_mp_indicators(mp)
    write_csv(mp, OUTPUT_DIR / "mp_risk_indicators.csv")

    write_csv(state_rollup(projects), OUTPUT_DIR / "state_rollup.csv")
    write_csv(category_rollup(projects), OUTPUT_DIR / "category_rollup.csv")
    write_csv(district_rollup(projects), OUTPUT_DIR / "constituency_rollup.csv")

    checks = validate_projects(projects)
    write_csv(checks, OUTPUT_DIR / "project_validation.csv")

    summary_obj = {
        "recommendations": int(len(rec)), "completed_works": int(len(comp)), "expenditures": int(len(exp)),
        "tier1_matches": int((matches["match_tier"]=="Tier 1").sum()),
        "tier2_matches": int((matches["match_tier"]=="Tier 2").sum()),
        "unmatched": int((matches["match_tier"]=="Unmatched").sum()),
        "high_risk_projects": int((projects["risk_level"]=="HIGH").sum()),
        "medium_risk_projects": int((projects["risk_level"]=="MEDIUM").sum()),
        "low_risk_projects": int((projects["risk_level"]=="LOW").sum()),
        "notes": "Risk flags are anomaly/risk indicators, not proof or probability of fraud. Expenditure evidence is aggregated at MP/IDA level because expenditure data lacks Work ID.",
    }
    with open(OUTPUT_DIR / "pipeline_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_obj, f, indent=2)
    return summary_obj
