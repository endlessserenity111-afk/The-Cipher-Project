from pathlib import Path
import pandas as pd


def review_metrics(df: pd.DataFrame) -> pd.DataFrame:
    x=df.copy(); x["human_verdict"]=x["human_verdict"].fillna("").astype(str).str.upper()
    rows=[]
    for tier in ["Tier 1","Tier 2"]:
        g=x[(x.review_type=="matched") & (x.match_tier==tier)]
        r=g[g.human_verdict.isin(["ACCEPT","REJECT"])]
        n=len(r); a=int((r.human_verdict=="ACCEPT").sum()); rej=int((r.human_verdict=="REJECT").sum())
        rows.append({"metric_group":tier,"reviewed":n,"accepted":a,"rejected":rej,"precision_pct":round(100*a/n,2) if n else None})
    u=x[x.review_type=="unmatched"]
    ur=u[u.human_verdict.isin(["ACCEPT","REJECT"])]
    recovered=int((ur.human_verdict=="ACCEPT").sum()); correct_unmatched=int((ur.human_verdict=="REJECT").sum()); total=len(ur)
    rows.append({"metric_group":"Unmatched review","reviewed":total,"accepted_as_recovered":recovered,"correctly_unmatched":correct_unmatched,"recovery_pct":round(100*recovered/total,2) if total else None})
    all_matched=x[(x.review_type=="matched") & (x.human_verdict.isin(["ACCEPT","REJECT"]))]
    aa=int((all_matched.human_verdict=="ACCEPT").sum()); an=len(all_matched)
    rows.append({"metric_group":"All reviewed matches","reviewed":an,"accepted":aa,"rejected":an-aa,"precision_pct":round(100*aa/an,2) if an else None})
    return pd.DataFrame(rows)


def write_review_metrics(input_path: Path, output_path: Path) -> pd.DataFrame:
    df=pd.read_csv(input_path)
    out=review_metrics(df)
    Path(output_path).parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(output_path,index=False)
    return out
