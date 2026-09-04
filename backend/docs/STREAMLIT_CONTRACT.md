# Streamlit contract

The frontend should read only generated outputs, not raw CSVs.

Main project file: `data/outputs/project_risk_scores.csv`

Important columns:
- recommendation_work_id
- completion_work_id
- mp_name
- constituency
- state
- category
- recommended_amount
- final_amount
- amount_difference_pct
- days_to_completion
- match_score
- match_tier
- match_confidence
- cost_percentile
- duration_percentile
- duration_ratio_to_peer_median
- ml_anomaly_score
- ml_anomaly_flag
- risk_score
- risk_level
- risk_reasons

MP financial file: `data/outputs/mp_risk_indicators.csv`

Important MP columns:
- mp_name
- constituency
- state
- top_vendor
- top_vendor_share_pct
- payment_mismatch_groups
- max_payment_completion_difference_pct
- reconciliation_difference_pct
- mp_risk_score
- mp_risk_level
- mp_risk_reasons

Safety language in UI:
"Risk indicator" / "Anomaly detected" / "May require verification"
Avoid claiming that the system proves fraud.
