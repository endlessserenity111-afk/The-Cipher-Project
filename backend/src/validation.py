import pandas as pd


def validate_matches(matches: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    accepted = matches[matches["completion_index"] >= 0]
    rows.append({"check":"accepted match scores in range","passed":matches["match_score"].between(0,100).all(),"detail":"Match scores must stay between 0 and 100."})
    rows.append({"check":"valid tiers","passed":matches["match_tier"].isin(["Tier 1","Tier 2","Unmatched"]).all(),"detail":"Only supported match tiers are allowed."})
    rows.append({"check":"no duplicate completion assignments","passed":accepted["completion_index"].is_unique,"detail":"Each accepted completion should map to at most one recommendation."})
    rows.append({"check":"unmatched rows have nonpositive completion index","passed":(matches.loc[matches["match_tier"]=="Unmatched","completion_index"] < 0).all(),"detail":"Unmatched rows should not carry an accepted completion index."})
    return pd.DataFrame(rows)


def validate_projects(projects: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    rows.append({"check":"risk score range","passed":projects["risk_score"].between(0,100).all(),"detail":"Risk score must be 0-100."})
    rows.append({"check":"valid risk levels","passed":projects["risk_level"].isin(["LOW","MEDIUM","HIGH"]).all(),"detail":"Risk level must be LOW/MEDIUM/HIGH."})
    rows.append({"check":"unique recommendation rows","passed":projects["recommendation_row_id"].is_unique,"detail":"One output row should represent one matched recommendation."})
    rows.append({"check":"non-negative financial values","passed":(projects[["recommended_amount","final_amount"]].fillna(0) >= 0).all().all(),"detail":"Amounts should not be negative."})
    # A large negative duration is a linkage/date-order problem.
    neg = pd.to_numeric(projects["days_to_completion"], errors="coerce") < -30
    rows.append({"check":"no large negative durations","passed":not neg.any(),"detail":"A completion should not be recorded substantially before the recommendation."})
    return pd.DataFrame(rows)


def validate_outputs(projects: pd.DataFrame, mp: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    rows.append({"check":"project output nonempty","passed":not projects.empty,"detail":"At least one accepted project match is needed for project-level analysis."})
    rows.append({"check":"MP output nonempty","passed":not mp.empty,"detail":"MP-level expenditure indicators should exist when expenditure data is available."})
    return pd.DataFrame(rows)
