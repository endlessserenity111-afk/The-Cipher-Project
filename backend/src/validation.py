import pandas as pd


def validate_projects(df: pd.DataFrame) -> pd.DataFrame:
    checks = []
    def add(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
    add("risk score range", df["risk_score"].between(0,100).all(), "All project risk scores must be between 0 and 100.")
    add("valid risk levels", df["risk_level"].isin(["LOW","MEDIUM","HIGH"]).all(), "Risk level must be LOW/MEDIUM/HIGH.")
    add("non-negative amounts", (df[["recommended_amount","final_amount"]].fillna(0) >= 0).all().all(), "Amounts should not be negative.")
    add("unique recommendation IDs", df["recommendation_row_id"].is_unique, "One output row should represent one matched recommendation.")
    add("date order mostly sensible", (df["days_to_completion"].dropna() >= -30).mean() >= 0.95 if len(df) else True, "Large negative durations indicate problematic linkage/date interpretation.")
    return pd.DataFrame(checks)


def validate_matches(matches: pd.DataFrame) -> pd.DataFrame:
    valid = matches[matches["completion_index"] >= 0]
    return pd.DataFrame([
        {"check":"no duplicate completion assignments", "passed":valid["completion_index"].is_unique, "detail":"Completed records should not be assigned to more than one recommendation."},
        {"check":"match score range", "passed":matches["match_score"].between(0,100).all(), "detail":"Match scores are 0-100."},
        {"check":"valid tiers", "passed":matches["match_tier"].isin(["Tier 1","Tier 2","Unmatched"]).all(), "detail":"Only supported match tiers are allowed."},
    ])
