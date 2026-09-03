import numpy as np
import pandas as pd


def build_project_features(recommendations: pd.DataFrame, completions: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    r = recommendations.reset_index(drop=True).copy()
    c = completions.reset_index(drop=True).copy()
    m = matches.copy()
    matched = m[m["completion_index"] >= 0].copy()
    if matched.empty:
        return pd.DataFrame()
    rows = []
    for _, x in matched.iterrows():
        rr = r.iloc[int(x["recommendation_index"])]
        cc = c.iloc[int(x["completion_index"])]
        rec_amt = float(rr.get("recommended_amount", np.nan))
        final_amt = float(cc.get("final_amount", np.nan))
        amount_diff = final_amt - rec_amt if np.isfinite(rec_amt) and np.isfinite(final_amt) else np.nan
        amount_pct = amount_diff / rec_amt * 100 if np.isfinite(amount_diff) and rec_amt > 0 else np.nan
        rec_date = rr.get("recommendation_date")
        comp_date = cc.get("completed_date")
        days = (comp_date - rec_date).days if not pd.isna(rec_date) and not pd.isna(comp_date) else np.nan
        rows.append({
            "recommendation_row_id": int(x["recommendation_index"]),
            "recommendation_work_id": rr.get("work_id"),
            "completion_row_id": int(x["completion_index"]),
            "completion_work_id": cc.get("work_id"),
            "mp_name": rr.get("mp_name", rr.get("MP Name", "")),
            "constituency": rr.get("constituency", ""),
            "state": rr.get("state", ""),
            "category": rr.get("category", ""),
            "ida": rr.get("ida", ""),
            "work_description": rr.get("work_description", ""),
            "recommended_amount": rec_amt,
            "final_amount": final_amt,
            "amount_difference": amount_diff,
            "amount_difference_pct": amount_pct,
            "recommendation_date": rec_date,
            "completion_date": comp_date,
            "days_to_completion": days,
            "match_score": x["match_score"],
            "match_tier": x["match_tier"],
            "match_confidence": x["match_confidence"],
            "score_margin": x["score_margin"],
            "match_reason": x["match_reason"],
        })
    return pd.DataFrame(rows)
