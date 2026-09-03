import pandas as pd


def state_rollup(projects: pd.DataFrame) -> pd.DataFrame:
    return projects.groupby("state", dropna=False).agg(
        projects=("recommendation_row_id","count"),
        high_risk_projects=("risk_level",lambda s:(s=="HIGH").sum()),
        medium_risk_projects=("risk_level",lambda s:(s=="MEDIUM").sum()),
        avg_risk_score=("risk_score","mean"),
        avg_cost_difference_pct=("amount_difference_pct","mean"),
    ).reset_index().sort_values("avg_risk_score", ascending=False)


def category_rollup(projects: pd.DataFrame) -> pd.DataFrame:
    return projects.groupby("category", dropna=False).agg(
        projects=("recommendation_row_id","count"),
        high_risk_projects=("risk_level",lambda s:(s=="HIGH").sum()),
        avg_risk_score=("risk_score","mean"),
        avg_cost_difference_pct=("amount_difference_pct","mean"),
        avg_days_to_completion=("days_to_completion","mean"),
    ).reset_index().sort_values("avg_risk_score", ascending=False)


def district_rollup(projects: pd.DataFrame) -> pd.DataFrame:
    return projects.groupby(["state","constituency"], dropna=False).agg(
        projects=("recommendation_row_id","count"),
        high_risk_projects=("risk_level",lambda s:(s=="HIGH").sum()),
        avg_risk_score=("risk_score","mean"),
    ).reset_index().sort_values("avg_risk_score", ascending=False)
