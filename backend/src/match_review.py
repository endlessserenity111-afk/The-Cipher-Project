from pathlib import Path
import html
import pandas as pd

REVIEW_COLUMNS = [
    "review_id", "review_type", "match_tier", "match_confidence", "match_score", "score_margin",
    "recommendation_index", "completion_index", "best_candidate_index", "best_candidate_score",
    "recommendation_work_id", "completion_work_id", "recommendation_description", "completion_description",
    "best_candidate_description", "recommendation_mp", "completion_mp", "best_candidate_mp",
    "recommendation_state", "completion_state", "recommendation_constituency", "completion_constituency",
    "recommendation_category", "completion_category", "recommendation_ida", "completion_ida",
    "recommended_amount", "final_amount", "timeline_match_score", "description_similarity", "mp_similarity",
    "constituency_similarity", "state_similarity", "ida_similarity", "category_similarity", "amount_similarity",
    "project_token_overlap", "match_reason", "human_verdict", "human_notes",
]


def _parse_reason(reason: str) -> dict:
    out = {}
    for part in str(reason).split("; "):
        if "=" in part:
            key, val = part.split("=", 1)
            try:
                out[key] = float(val)
            except ValueError:
                pass
    return out


def _sample_tier(matches: pd.DataFrame, tier: str, seed: int = 42, random_n: int = 5, borderline_n: int = 3, strong_n: int = 2) -> pd.DataFrame:
    x = matches[matches["match_tier"] == tier].copy()
    if x.empty:
        return x
    n_random = min(random_n, len(x))
    parts = [x.sample(n=n_random, random_state=seed)]
    used = set(parts[0].index)
    remaining = x.loc[~x.index.isin(used)]
    parts.append(remaining.sort_values(["match_score", "score_margin"]).head(min(borderline_n, len(remaining))))
    used.update(parts[-1].index)
    remaining = x.loc[~x.index.isin(used)]
    parts.append(remaining.sort_values(["match_score", "score_margin"], ascending=False).head(min(strong_n, len(remaining))))
    return pd.concat(parts).drop_duplicates().reset_index(drop=True)


def _sample_unmatched(matches: pd.DataFrame, seed: int = 42, n_random: int = 5, n_borderline: int = 3, n_low_conf: int = 2) -> pd.DataFrame:
    x = matches[matches["match_tier"] == "Unmatched"].copy()
    if x.empty:
        return x
    parts=[]; used=set()
    a=x.sample(n=min(n_random,len(x)), random_state=seed); parts.append(a); used.update(a.index)
    rem=x.loc[~x.index.isin(used)].sort_values("best_candidate_score", ascending=False)
    b=rem.head(min(n_borderline,len(rem))); parts.append(b); used.update(b.index)
    rem=x.loc[~x.index.isin(used)].sort_values("best_candidate_score", ascending=True)
    parts.append(rem.head(min(n_low_conf,len(rem))))
    return pd.concat(parts).drop_duplicates().reset_index(drop=True)


def _field(row, *names):
    for name in names:
        if name in row.index:
            return row.get(name, "")
    return ""


def build_review_samples(matches: pd.DataFrame, recommendations: pd.DataFrame, completions: pd.DataFrame, output_dir: Path, seed: int = 42) -> dict:
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    rows=[]
    review_id=1
    for tier in ["Tier 1", "Tier 2"]:
        sampled=_sample_tier(matches,tier,seed)
        for _, m in sampled.iterrows():
            rr=recommendations.iloc[int(m["recommendation_index"])]
            ci=int(m["completion_index"])
            cc=completions.iloc[ci] if ci >= 0 else None
            ev=_parse_reason(m["match_reason"])
            rows.append({
                "review_id":review_id,"review_type":"matched","match_tier":m["match_tier"],"match_confidence":m["match_confidence"],
                "match_score":m["match_score"],"score_margin":m["score_margin"],"recommendation_index":int(m["recommendation_index"]),
                "completion_index":ci,"best_candidate_index":int(m.get("best_candidate_index",-1)),"best_candidate_score":m.get("best_candidate_score",0),
                "recommendation_work_id":_field(rr,"work_id"),"completion_work_id":_field(cc,"work_id") if cc is not None else "",
                "recommendation_description":_field(rr,"work_description"),"completion_description":_field(cc,"work_description") if cc is not None else "",
                "best_candidate_description":"","recommendation_mp":_field(rr,"mp_name"),"completion_mp":_field(cc,"mp_name") if cc is not None else "",
                "best_candidate_mp":"","recommendation_state":_field(rr,"state"),"completion_state":_field(cc,"state") if cc is not None else "",
                "recommendation_constituency":_field(rr,"constituency"),"completion_constituency":_field(cc,"constituency") if cc is not None else "",
                "recommendation_category":_field(rr,"category"),"completion_category":_field(cc,"category") if cc is not None else "",
                "recommendation_ida":_field(rr,"ida"),"completion_ida":_field(cc,"ida") if cc is not None else "",
                "recommended_amount":_field(rr,"recommended_amount"),"final_amount":_field(cc,"final_amount") if cc is not None else "",
                "timeline_match_score":ev.get("timeline", ""),"description_similarity":ev.get("description", ""),"mp_similarity":ev.get("mp", ""),
                "constituency_similarity":ev.get("constituency", ""),"state_similarity":ev.get("state", ""),"ida_similarity":ev.get("ida", ""),
                "category_similarity":ev.get("category", ""),"amount_similarity":ev.get("amount", ""),"project_token_overlap":ev.get("token_overlap", ""),
                "match_reason":m["match_reason"],"human_verdict":"","human_notes":"",
            }); review_id+=1
    sampled=_sample_unmatched(matches,seed)
    for _, m in sampled.iterrows():
        rr=recommendations.iloc[int(m["recommendation_index"])]
        bi=int(m.get("best_candidate_index",-1))
        bc=completions.iloc[bi] if bi>=0 else None
        rows.append({
            "review_id":review_id,"review_type":"unmatched","match_tier":"Unmatched","match_confidence":"Unmatched","match_score":0.0,
            "score_margin":m.get("score_margin",0),"recommendation_index":int(m["recommendation_index"]),"completion_index":-1,"best_candidate_index":bi,
            "best_candidate_score":m.get("best_candidate_score",0),"recommendation_work_id":_field(rr,"work_id"),"completion_work_id":"",
            "recommendation_description":_field(rr,"work_description"),"completion_description":"","best_candidate_description":_field(bc,"work_description") if bc is not None else "",
            "recommendation_mp":_field(rr,"mp_name"),"completion_mp":"","best_candidate_mp":_field(bc,"mp_name") if bc is not None else "",
            "recommendation_state":_field(rr,"state"),"completion_state":"","recommendation_constituency":_field(rr,"constituency"),"completion_constituency":"",
            "recommendation_category":_field(rr,"category"),"completion_category":"","recommendation_ida":_field(rr,"ida"),"completion_ida":"",
            "recommended_amount":_field(rr,"recommended_amount"),"final_amount":"","timeline_match_score":"","description_similarity":"","mp_similarity":"",
            "constituency_similarity":"","state_similarity":"","ida_similarity":"","category_similarity":"","amount_similarity":"",
            "project_token_overlap":"","match_reason":m["match_reason"],"human_verdict":"","human_notes":"",
        }); review_id+=1

    review=pd.DataFrame(rows, columns=REVIEW_COLUMNS)

    # Preserve prior human verdicts/notes when rerunning the pipeline.
    previous_path=output_dir/"match_review.csv"
    if previous_path.exists():
        try:
            prev=pd.read_csv(previous_path)
            key=["review_type","recommendation_index","completion_index","best_candidate_index"]
            available=prev[key+['human_verdict','human_notes']].drop_duplicates(key)
            review=review.drop(columns=["human_verdict","human_notes"]).merge(available,on=key,how="left")
            review[["human_verdict","human_notes"]]=review[["human_verdict","human_notes"]].fillna("")
            review=review[REVIEW_COLUMNS]
        except Exception:
            pass

    review.to_csv(previous_path,index=False)
    review[review.match_tier=="Tier 1"].to_csv(output_dir/"tier1_review_sample.csv",index=False)
    review[review.match_tier=="Tier 2"].to_csv(output_dir/"tier2_review_sample.csv",index=False)
    review[review.review_type=="unmatched"].to_csv(output_dir/"unmatched_review_sample.csv",index=False)
    write_html(review, output_dir/"match_review.html")
    return {
        "tier1_review_rows": int((review.match_tier=="Tier 1").sum()),
        "tier2_review_rows": int((review.match_tier=="Tier 2").sum()),
        "unmatched_review_rows": int((review.review_type=="unmatched").sum()),
        "review_rows": int(len(review)),
    }


def write_html(df: pd.DataFrame, path: Path) -> None:
    cards=[]
    for _, r in df.iterrows():
        if r.review_type == "unmatched":
            evidence=f"<div class='warning'><b>Best rejected candidate</b><br>{html.escape(str(r.best_candidate_description))}<br><small>Score: {html.escape(str(r.best_candidate_score))}</small></div>"
        else:
            metrics=[]
            for key,label in [
                ("description_similarity","Description"),("mp_similarity","MP"),("constituency_similarity","Constituency"),
                ("state_similarity","State"),("ida_similarity","IDA"),("category_similarity","Category"),
                ("amount_similarity","Amount"),("timeline_match_score","Timeline"),
            ]:
                val=r.get(key,"")
                if val != "" and not pd.isna(val): metrics.append(f"<div class='metric'><span>{label}</span><b>{float(val):.1f}</b></div>")
            evidence=f"<div class='grid'>{''.join(metrics)}</div>"
        card=f"""
        <article class='card'>
          <div class='top'><span class='tier'>{html.escape(str(r.match_tier))}</span><b>Score {float(r.match_score or 0):.2f}</b></div>
          <h2>Recommendation</h2><p>{html.escape(str(r.recommendation_description))}</p>
          <div class='meta'>{html.escape(str(r.recommendation_mp))} · {html.escape(str(r.recommendation_constituency))} · {html.escape(str(r.recommendation_state))}</div>
          <h2>{'Best candidate' if r.review_type=='unmatched' else 'Matched completion'}</h2>
          <p>{html.escape(str(r.completion_description if r.review_type!='unmatched' else r.best_candidate_description))}</p>
          <div class='meta'>{html.escape(str(r.completion_mp if r.review_type!='unmatched' else r.best_candidate_mp))}</div>
          {evidence}
          <div class='reason'><b>System evidence:</b> {html.escape(str(r.match_reason))}</div>
        </article>"""
        cards.append(card)
    doc=f"""<!doctype html><html><head><meta charset='utf-8'><title>MPLADS Match Review</title>
    <style>body{{font-family:Arial,sans-serif;max-width:1100px;margin:25px auto;background:#f4f5f7;color:#222;padding:0 15px}}h1{{margin-bottom:5px}}.note{{color:#555}}.card{{background:#fff;border:1px solid #ddd;border-radius:12px;margin:18px 0;padding:20px;box-shadow:0 2px 6px rgba(0,0,0,.04)}}.top{{display:flex;justify-content:space-between;border-bottom:1px solid #eee;padding-bottom:10px}}.tier{{font-weight:700}}.meta{{color:#667085;font-size:14px;margin-bottom:13px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:15px 0}}.metric{{background:#f7f8fa;padding:8px;border-radius:7px;display:flex;justify-content:space-between}}.reason,.warning{{background:#f7f8fa;padding:12px;border-radius:8px;font-size:14px}}.warning{{background:#fff4e5}}small{{color:#667085}}@media(max-width:700px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}</style>
    </head><body><h1>MPLADS Match Review</h1><p class='note'>Human review aid. A match is a linkage assessment, not a fraud finding.</p>{''.join(cards)}</body></html>"""
    Path(path).write_text(doc, encoding="utf-8")
