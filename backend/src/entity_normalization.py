import re
import pandas as pd
from .cleaning import normalize_text, normalize_key


def canonicalize_mp(name: str) -> str:
    s = normalize_text(name)
    s = re.sub(r"^(shri|smt|mr|ms|dr)\.?\s+", "", s)
    return s.strip()


def canonicalize_constituency(name: str) -> str:
    s = normalize_text(name)
    s = re.sub(r"\s*-?\s*\d+\s*$", "", s)
    return s.strip()


def normalize_entities(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    mapping = {
        "MP Name": "mp_norm",
        "Constituency": "constituency_norm",
        "State": "state_norm",
        "House": "house_norm",
        "IDA": "ida_norm",
        "Vendor": "vendor_norm",
        "Category": "category_norm",
        "Work Description": "work_norm",
        "Work ID": "work_id_norm",
    }
    for source, target in mapping.items():
        if source in out.columns:
            out[target] = out[source].map(normalize_text)
            out[target + "_key"] = out[target].map(normalize_key)
    if "MP Name" in out.columns:
        out["mp_canonical"] = out["MP Name"].map(canonicalize_mp)
        out["mp_canonical_key"] = out["mp_canonical"].map(normalize_key)
    if "Constituency" in out.columns:
        out["constituency_canonical"] = out["Constituency"].map(canonicalize_constituency)
        out["constituency_canonical_key"] = out["constituency_canonical"].map(normalize_key)
    return out
