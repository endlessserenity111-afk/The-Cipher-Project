import re
import pandas as pd
from .cleaning import normalize_text, normalize_key


def normalize_entities(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    text_map = {
        "MP Name": "mp_norm",
        "Constituency": "constituency_norm",
        "State": "state_norm",
        "House": "house_norm",
        "IDA": "ida_norm",
        "Vendor": "vendor_norm",
        "Category": "category_norm",
        "Work Description": "work_norm",
    }
    for source, target in text_map.items():
        if source in out.columns:
            out[target] = out[source].map(normalize_text)
            out[target + "_key"] = out[target].map(normalize_key)
    return out


def canonicalize_mp(name: str) -> str:
    s = normalize_text(name)
    s = re.sub(r"^(shri|smt|mr|ms|dr)\.?\s+", "", s)
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)
    return s.strip()


def canonicalize_constituency(name: str) -> str:
    s = normalize_text(name)
    s = re.sub(r"\s*-?\s*\d+\s*$", "", s)
    return s.strip()


def add_canonical_entities(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "MP Name" in out.columns:
        out["mp_canonical"] = out["MP Name"].map(canonicalize_mp)
    if "Constituency" in out.columns:
        out["constituency_canonical"] = out["Constituency"].map(canonicalize_constituency)
    return out
