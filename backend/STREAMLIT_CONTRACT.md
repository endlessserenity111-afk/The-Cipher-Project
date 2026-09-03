# Streamlit backend contract

The frontend should **not calculate fraud/anomaly logic**. It should read the exported backend files.

## Main project table

`data/outputs/project_risk_scores.csv`

Key fields:
- `recommendation_row_id` — unique row identifier in the source recommendation table
- `recommendation_work_id` — source Work ID; not assumed globally unique across tables
- `completion_work_id` — source completed-work Work ID; not assumed globally unique
- `mp_name`, `constituency`, `state`, `category`, `ida`
- `recommended_amount`, `final_amount`, `amount_difference`, `amount_difference_pct`
- `recommendation_date`, `completion_date`, `days_to_completion`
- `match_score`, `match_tier`, `match_confidence`, `score_margin`, `match_reason`
- `amount_difference_pct_iqr_flag`, `days_to_completion_iqr_flag`
- `ml_anomaly_score`, `ml_anomaly_flag`
- `risk_score`, `risk_level`, `risk_reasons`

## MP financial indicators

`data/outputs/mp_risk_indicators.csv`

Use for MP-level cards/tables:
- top vendor and share
- total paid vs completed value
- mismatch group count
- MP risk score/level/reasons

## Rollups

- `state_rollup.csv`
- `category_rollup.csv`
- `constituency_rollup.csv`

## Matching diagnostics

`match_results.csv` contains all recommendations and their final linkage state.

## Safety/interpretation

The UI should call the result an **anomaly/risk assessment**. Do not label a row as proven fraud. Tier 2 is provisional evidence and should be visibly differentiated from Tier 1.
