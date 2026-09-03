import argparse
import json
import config
from src import pipeline


def main():
    parser = argparse.ArgumentParser(description="Run the SIH26102 MPLADS backend pipeline.")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N recommendations (good for testing).")
    args = parser.parse_args()

    # Temporary test limit: keep the production defaults untouched.
    if args.limit:
        original_run = pipeline.run_pipeline
        def limited_run():
            import pandas as pd
            from src.io_utils import ensure_dirs, read_csv, write_csv
            from src.pipeline import (standardize_recommendations, standardize_completions,
                                      standardize_expenditures, standardize_mp_summary)
            from src.cleaning import build_quality_report
            from src.matching import match_records
            from src.feature_engineering import build_project_features
            from src.anomaly_detection import add_statistical_anomalies, add_isolation_forest
            from src.risk_scoring import score_projects, score_mp_indicators
            from src.expenditure_checks import build_mp_indicators
            from src.aggregations import state_rollup, category_rollup, district_rollup
            from src.validation import validate_projects, validate_matches
            from src.match_review import build_review_samples
            ensure_dirs(config.RAW_DIR, config.PROCESSED_DIR, config.OUTPUT_DIR)
            rec=standardize_recommendations(read_csv(config.RECOMMENDED_FILE).head(args.limit))
            comp=standardize_completions(read_csv(config.COMPLETED_FILE))
            exp=standardize_expenditures(read_csv(config.EXPENDITURE_FILE))
            summ=standardize_mp_summary(read_csv(config.MP_SUMMARY_FILE))
            write_csv(build_quality_report({"recommendations":rec,"completions":comp,"expenditures":exp,"mp_summary":summ}),config.OUTPUT_DIR/"data_quality_report.csv")
            matches=match_records(rec,comp); write_csv(matches,config.OUTPUT_DIR/"match_results.csv"); write_csv(validate_matches(matches),config.OUTPUT_DIR/"match_validation.csv"); review_summary=build_review_samples(matches,rec,comp,config.OUTPUT_DIR/"review")
            projects=build_project_features(rec,comp,matches)
            if projects.empty: raise RuntimeError("No project matches passed the threshold on this sample.")
            projects=score_projects(add_isolation_forest(add_statistical_anomalies(projects)))
            write_csv(projects,config.OUTPUT_DIR/"project_risk_scores.csv")
            write_csv(projects[projects.risk_level=="HIGH"],config.OUTPUT_DIR/"high_risk_projects.csv")
            mp=score_mp_indicators(build_mp_indicators(exp,projects)); write_csv(mp,config.OUTPUT_DIR/"mp_risk_indicators.csv")
            write_csv(state_rollup(projects),config.OUTPUT_DIR/"state_rollup.csv"); write_csv(category_rollup(projects),config.OUTPUT_DIR/"category_rollup.csv"); write_csv(district_rollup(projects),config.OUTPUT_DIR/"constituency_rollup.csv")
            write_csv(validate_projects(projects),config.OUTPUT_DIR/"project_validation.csv")
            out={"mode":"limited","limit":args.limit,"recommendations":len(rec),"completed_works":len(comp),"tier1_matches":int((matches.match_tier=="Tier 1").sum()),"tier2_matches":int((matches.match_tier=="Tier 2").sum()),"unmatched":int((matches.match_tier=="Unmatched").sum()),"high_risk_projects":int((projects.risk_level=="HIGH").sum()),"review":review_summary}
            with open(config.OUTPUT_DIR/"pipeline_summary.json","w",encoding="utf-8") as f: json.dump(out,f,indent=2)
            return out
        summary=limited_run()
    else:
        summary=original_run()
    print("\nMPLADS backend pipeline completed.\n")
    print(json.dumps(summary,indent=2))

if __name__ == "__main__":
    main()
