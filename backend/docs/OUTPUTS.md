# Output guide

`project_risk_scores.csv` — project-level linked works and risk evidence.

`high_risk_projects.csv` — filtered project-level output where risk level is HIGH.

`mp_risk_indicators.csv` — MP/constituency financial indicators including vendor concentration, payment/completion mismatch groups, and summary reconciliation differences.

`match_results.csv` — one row per recommendation with accepted completion index (or -1), score, tier, confidence, margin, best candidate, and reason.

`data_quality_report.csv` — field-level missingness, blank counts, unique values, and duplicate-row count.

`review/match_review.csv` — human review queue for Tier 1, Tier 2, and unmatched examples.

`review/match_review.html` — browser-friendly review cards.

`review/match_review_metrics.csv` — human-review precision and unmatched recovery metrics.

`state_rollup.csv`, `category_rollup.csv`, `constituency_rollup.csv` — summary views for Streamlit.

`pipeline_summary.json` — run counts, runtime, and interpretation notes.

`pipeline_manifest.json` — input file hashes plus key configuration values for reproducibility.
