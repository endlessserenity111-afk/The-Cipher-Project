import pandas as pd
from src.match_metrics import review_metrics


def test_review_metrics():
    df=pd.DataFrame([
        {'review_type':'matched','match_tier':'Tier 1','human_verdict':'ACCEPT'},
        {'review_type':'matched','match_tier':'Tier 1','human_verdict':'REJECT'},
        {'review_type':'unmatched','match_tier':'Unmatched','human_verdict':'ACCEPT'},
        {'review_type':'unmatched','match_tier':'Unmatched','human_verdict':'REJECT'},
    ])
    out=review_metrics(df)
    assert float(out.loc[out.metric_group=='Tier 1','precision_pct'].iloc[0]) == 50.0
    assert float(out.loc[out.metric_group=='Unmatched review','recovery_pct'].iloc[0]) == 50.0
