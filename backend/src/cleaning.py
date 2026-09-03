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
    return pd.to_datetime(series, errors="coerce", utc=True).dt.tz_convert(None)


def clean_money(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False)
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


def add_normalized_columns(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    for source, target in mapping.items():
        if source in out.columns:
            out[target] = out[source].map(normalize_text)
    return out


def build_quality_report(frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in frames.items():
        for col in df.columns:
            nulls = int(df[col].isna().sum())
            blanks = int((df[col].astype(str).str.strip() == "").sum()) if df[col].dtype == "object" else 0
            rows.append({
                "dataset": name,
                "rows": len(df),
                "column": col,
                "dtype": str(df[col].dtype),
                "missing": nulls,
                "blank_strings": blanks,
                "missing_pct": round((nulls / len(df) * 100) if len(df) else 0, 3),
                "unique_values": int(df[col].nunique(dropna=False)),
            })
    return pd.DataFrame(rows)
