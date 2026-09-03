import pandas as pd
from src.match_metrics import review_metrics

def test_metrics():
    d=pd.DataFrame([{'match_tier':'Tier 1','human_verdict':'ACCEPT'},{'match_tier':'Tier 1','human_verdict':'REJECT'}]); x=review_metrics(d); assert x.loc[x.tier.eq('Tier 1'),'precision_pct'].iloc[0]==50.0
