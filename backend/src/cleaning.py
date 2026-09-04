import re
import unicodedata
from typing import Dict
import numpy as np
import pandas as pd


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"[^a-z0-9\u0900-\u097f\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_key(value) -> str:
    text = normalize_text(value)
    return re.sub(r"[^a-z0-9]", "", text)


def parse_date(series: pd.Series) -> pd.Series:
    # Day-first is useful for Indian date exports while ISO still parses correctly.
    return pd.to_datetime(series, errors="coerce", format="mixed")


def clean_money(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False)
    s = s.replace({"": np.nan, "nan": np.nan, "None": np.nan})
    return pd.to_numeric(s, errors="coerce")


def basic_cleaning(df: pd.DataFrame, money_cols=None, date_cols=None, text_cols=None) -> pd.DataFrame:
    out = df.copy()
    money_cols = money_cols or []
    date_cols = date_cols or []
    text_cols = text_cols or []
    out.columns = [str(c).strip() for c in out.columns]
    for c in money_cols:
        if c in out.columns:
            out[c] = clean_money(out[c])
    for c in date_cols:
        if c in out.columns:
            out[c] = parse_date(out[c])
    for c in text_cols:
        if c in out.columns:
            out[c] = out[c].fillna("").astype(str).str.strip()
    return out


def build_quality_report(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in frames.items():
        duplicate_rows = int(df.duplicated().sum())
        for col in df.columns:
            missing = int(df[col].isna().sum())
            blank = int((df[col].astype(str).str.strip() == "").sum()) if df[col].dtype == "object" else 0
            rows.append({
                "dataset": name,
                "rows": len(df),
                "columns": len(df.columns),
                "column": col,
                "dtype": str(df[col].dtype),
                "missing": missing,
                "blank_strings": blank,
                "missing_pct": round(missing / len(df) * 100, 3) if len(df) else 0.0,
                "unique_values": int(df[col].nunique(dropna=False)),
                "duplicate_rows_in_dataset": duplicate_rows,
            })
    return pd.DataFrame(rows)


def build_dataset_summary(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in frames.items():
        rows.append({
            "dataset": name,
            "rows": len(df),
            "columns": len(df.columns),
            "duplicate_rows": int(df.duplicated().sum()),
        })
    return pd.DataFrame(rows)
