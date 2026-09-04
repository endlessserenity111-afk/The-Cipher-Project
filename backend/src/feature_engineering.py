import numpy as np
import pandas as pd


def build_project_features(recommendations: pd.DataFrame, completions: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    rec = recommendations.reset_index(drop=True)
    comp = completions.reset_index(drop=True)
    matched = matches[matches["completion_index"] >= 0].copy()
    rows = []
    for _, m in matched.iterrows():
        rr = rec.iloc[int(m["recommendation_index"])]
        cc = comp.iloc[int(m["completion_index"])]
        rec_amt = pd.to_numeric(rr.get("recommended_amount"), errors="coerce")
        final_amt = pd.to_numeric(cc.get("final_amount"), errors="coerce")
        diff = final_amt - rec_amt if pd.notna(rec_amt) and pd.notna(final_amt) else np.nan
        diff_pct = diff / rec_amt * 100 if pd.notna(diff) and rec_amt > 0 else np.nan
        rec_date = rr.get("recommendation_date")
        comp_date = cc.get("completed_date")
        days = (comp_date - rec_date).days if pd.notna(rec_date) and pd.notna(comp_date) else np.nan
        rows.append({
            "recommendation_row_id": int(m["recommendation_index"]),
            "recommendation_work_id": rr.get("work_id", ""),
            "completion_row_id": int(m["completion_index"]),
            "completion_work_id": cc.get("work_id", ""),
            "mp_name": rr.get("mp_name", ""),
            "constituency": rr.get("constituency", ""),
            "state": rr.get("state", ""),
            "category": rr.get("category", ""),
            "ida": rr.get("ida", ""),
            "work_description": rr.get("work_description", ""),
            "recommended_amount": rec_amt,
            "final_amount": final_amt,
            "amount_difference": diff,
            "amount_difference_pct": diff_pct,
            "recommendation_date": rec_date,
            "completion_date": comp_date,
            "days_to_completion": days,
            "match_score": float(m["match_score"]),
            "match_tier": m["match_tier"],
            "match_confidence": m["match_confidence"],
            "score_margin": float(m["score_margin"]),
            "match_reason": m["match_reason"],
            "has_images": cc.get("Has Images"),  # standardize_completions() keeps this column as-is
        })
    return pd.DataFrame(rows)


def add_peer_features(projects: pd.DataFrame, min_group: int = 15) -> pd.DataFrame:
    out = projects.copy()
    if out.empty:
        return out
    out["positive_amount_difference_pct"] = pd.to_numeric(out["amount_difference_pct"], errors="coerce").clip(lower=0)
    out["days_to_completion"] = pd.to_numeric(out["days_to_completion"], errors="coerce")

    keys = ["state", "category"]
    group = out.groupby(keys, dropna=False)
    counts = group["recommendation_row_id"].transform("count")
    fallback = out.groupby(["category"], dropna=False)["recommendation_row_id"].transform("count") >= min_group
    use_peer = counts >= min_group

    out["peer_group"] = np.where(use_peer, out["state"].astype(str) + " | " + out["category"].astype(str), out["category"].astype(str))

    def group_stat(frame, col, stat):
        g = frame.groupby(["state", "category"], dropna=False)[col].transform(stat)
        fallback_val = frame.groupby(["category"], dropna=False)[col].transform(stat)
        return g.where(use_peer, fallback_val)

    for col, prefix in [("positive_amount_difference_pct", "cost_peer"), ("days_to_completion", "duration_peer")]:
        out[prefix + "_median"] = group_stat(out, col, "median")
        out[prefix + "_p75"] = group_stat(out, col, lambda s: s.quantile(0.75))
        out[prefix + "_p95"] = group_stat(out, col, lambda s: s.quantile(0.95))

    out["duration_ratio_to_peer_median"] = np.where(
        out["duration_peer_median"].fillna(0) > 0,
        out["days_to_completion"] / out["duration_peer_median"],
        np.nan,
    )
    out["cost_ratio_to_peer_median"] = np.where(
        out["cost_peer_median"].fillna(0) > 0,
        out["positive_amount_difference_pct"] / out["cost_peer_median"],
        np.nan,
    )

    for value_col, pct_col in [("positive_amount_difference_pct", "cost_percentile"), ("days_to_completion", "duration_percentile")]:
        out[pct_col] = out.groupby(["peer_group"], dropna=False)[value_col].rank(pct=True) * 100
    return out
