import pandas as pd
from src.risk_scoring import score_projects


def test_risk_score_range_and_level():
    df=pd.DataFrame([{
        'positive_amount_difference_pct':80,'amount_difference_pct_iqr_flag':True,'cost_percentile':99,
        'days_to_completion':700,'days_to_completion_iqr_flag':True,'duration_percentile':99,'duration_ratio_to_peer_median':2.5,
        'ml_anomaly_flag':True,'match_tier':'Tier 1'
    }])
    out=score_projects(df)
    assert 0 <= float(out.loc[0,'risk_score']) <= 100
    assert out.loc[0,'risk_level'] in {'LOW','MEDIUM','HIGH'}
