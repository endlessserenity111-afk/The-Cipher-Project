import pandas as pd
from src.matching import match_records


def test_matching_returns_expected_columns():
    rec = pd.DataFrame([{
        "work_norm":"construction community hall near village alpha",
        "mp_norm":"test mp", "constituency_norm":"alpha", "state_norm":"test state",
        "ida_norm":"district authority", "category_norm":"normal others",
        "recommended_amount":500000.0, "recommendation_date":pd.Timestamp("2025-01-01")
    }])
    comp = pd.DataFrame([{
        "work_norm":"Construction of community hall near Village Alpha",
        "mp_norm":"test mp", "constituency_norm":"alpha", "state_norm":"test state",
        "ida_norm":"district authority", "category_norm":"normal others",
        "final_amount":490000.0, "completed_date":pd.Timestamp("2025-04-01")
    }])
    out = match_records(rec, comp)
    assert {"match_score","match_tier","match_confidence","completion_index"}.issubset(out.columns)
    assert out.iloc[0]["completion_index"] == 0
