from pathlib import Path
import pandas as pd

def review_metrics(df):
    x=df.copy(); x['human_verdict']=x['human_verdict'].fillna('').astype(str).str.upper(); rows=[]
    for tier in ['Tier 1','Tier 2','ALL']:
        g=x if tier=='ALL' else x[x.match_tier.eq(tier)]; r=g[g.human_verdict.isin(['ACCEPT','REJECT'])]; n=len(r); a=int((r.human_verdict=='ACCEPT').sum()); rows.append({'tier':tier,'reviewed':n,'accepted':a,'rejected':int((r.human_verdict=='REJECT').sum()),'precision_pct':round(100*a/n,2) if n else None})
    return pd.DataFrame(rows)

def write_review_metrics(input_path,output_path):
    x=review_metrics(pd.read_csv(input_path)); Path(output_path).parent.mkdir(parents=True,exist_ok=True); x.to_csv(output_path,index=False); return x
