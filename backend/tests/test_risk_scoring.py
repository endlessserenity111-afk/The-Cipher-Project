import pandas as pd
from src.risk_scoring import score_projects


def test_high_cost_project_gets_risk():
    df = pd.DataFrame([{
        "amount_difference_pct":80.0,
        "amount_difference_pct_iqr_flag":True,
        "days_to_completion":600.0,
        "days_to_completion_iqr_flag":True,
        "ml_anomaly_flag":True,
        "match_tier":"Tier 1",
        "match_score":90.0,
    }])
    out = score_projects(df)
    assert out.iloc[0]["risk_level"] == "HIGH"
    assert out.iloc[0]["risk_score"] >= 70
