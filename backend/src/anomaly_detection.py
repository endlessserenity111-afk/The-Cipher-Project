import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from config import RANDOM_STATE


def _iqr_flag(series: pd.Series) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce")
    if x.notna().sum() < 15:
        return pd.Series(False, index=series.index)
    q1, q3 = x.quantile([0.25, 0.75])
    iqr = q3 - q1
    if not np.isfinite(iqr) or iqr == 0:
        return pd.Series(False, index=series.index)
    return x > q3 + 1.5 * iqr


def add_statistical_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["amount_difference_pct_iqr_flag"] = _iqr_flag(out["positive_amount_difference_pct"])
    out["days_to_completion_iqr_flag"] = _iqr_flag(out["days_to_completion"])
    out["cost_peer_high_flag"] = pd.to_numeric(out["cost_percentile"], errors="coerce") >= 95
    out["duration_peer_high_flag"] = pd.to_numeric(out["duration_percentile"], errors="coerce") >= 95
    out["duration_ratio_high_flag"] = pd.to_numeric(out["duration_ratio_to_peer_median"], errors="coerce") >= 2.0
    return out


def add_isolation_forest(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    cols = [
        "recommended_amount", "final_amount", "positive_amount_difference_pct",
        "days_to_completion", "cost_percentile", "duration_percentile",
        "duration_ratio_to_peer_median", "match_score", "score_margin",
    ]
    available = [c for c in cols if c in out.columns]
    if len(out) < 50 or not available:
        out["ml_anomaly_score"] = 0.0
        out["ml_anomaly_flag"] = False
        return out
    X = out[available].apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True)).fillna(0)
    Xs = RobustScaler().fit_transform(X)
    model = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    pred = model.fit_predict(Xs)
    decision = model.decision_function(Xs)
    out["ml_anomaly_score"] = np.round(-decision, 4)
    out["ml_anomaly_flag"] = pred == -1
    return out
