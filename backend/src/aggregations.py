import pandas as pd


def _rollup(projects, keys):
    if projects.empty:
        return pd.DataFrame(columns=keys + ["projects","high_risk_projects","medium_risk_projects","avg_risk_score","avg_cost_difference_pct","avg_days_to_completion"])
    out = projects.groupby(keys, dropna=False).agg(
        projects=("recommendation_row_id", "count"),
        high_risk_projects=("risk_level", lambda s: int((s == "HIGH").sum())),
        medium_risk_projects=("risk_level", lambda s: int((s == "MEDIUM").sum())),
        avg_risk_score=("risk_score", "mean"),
        avg_cost_difference_pct=("amount_difference_pct", "mean"),
        avg_days_to_completion=("days_to_completion", "mean"),
    ).reset_index()
    return out.sort_values("avg_risk_score", ascending=False)


def state_rollup(projects):
    return _rollup(projects, ["state"])


def category_rollup(projects):
    return _rollup(projects, ["category"])


def constituency_rollup(projects):
    return _rollup(projects, ["state", "constituency"])
