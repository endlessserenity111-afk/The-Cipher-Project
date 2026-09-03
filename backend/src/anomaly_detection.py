import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from config import RANDOM_STATE


def add_statistical_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["amount_difference_pct", "days_to_completion"]:
        x = pd.to_numeric(out[col], errors="coerce")
        if x.notna().sum() >= 20:
            q1, q3 = x.quantile([0.25, 0.75])
            iqr = q3 - q1
            upper = q3 + 1.5 * iqr
            out[col + "_iqr_flag"] = x > upper
        else:
            out[col + "_iqr_flag"] = False
    return out


def add_isolation_forest(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    feature_cols = [
        "recommended_amount", "final_amount", "amount_difference_pct",
        "days_to_completion", "match_score", "score_margin",
    ]
    available = [c for c in feature_cols if c in out.columns]
    work = out[available].apply(pd.to_numeric, errors="coerce")
    if len(work) < 50 or not available:
        out["ml_anomaly_score"] = 0.0
        out["ml_anomaly_flag"] = False
        return out
    X = work.replace([np.inf, -np.inf], np.nan).fillna(work.median(numeric_only=True)).fillna(0)
    Xs = StandardScaler().fit_transform(X)
    model = IsolationForest(n_estimators=250, contamination="auto", random_state=RANDOM_STATE, n_jobs=-1)
    pred = model.fit_predict(Xs)
    decision = model.decision_function(Xs)
    out["ml_anomaly_score"] = np.round(-decision, 4)
    out["ml_anomaly_flag"] = pred == -1
    return out
