import numpy as np
import pandas as pd
from config import PAYMENT_MISMATCH_MIN_ABS, PAYMENT_MISMATCH_MIN_PCT, VENDOR_CONCENTRATION_FLAG_PCT


def vendor_concentration(exp: pd.DataFrame) -> pd.DataFrame:
    e = exp.copy()
    e["amount_paid"] = pd.to_numeric(e["amount_paid"], errors="coerce").fillna(0)
    keys = ["mp_name", "constituency", "state"]
    total = e.groupby(keys, dropna=False)["amount_paid"].sum().rename("mp_total_spend").reset_index()
    v = e.groupby(keys + ["vendor_name"], dropna=False)["amount_paid"].sum().reset_index(name="vendor_spend")
    v = v.merge(total, on=keys, how="left")
    v["vendor_share_pct"] = np.where(v["mp_total_spend"] > 0, v["vendor_spend"] / v["mp_total_spend"] * 100, np.nan)
    v = v.sort_values(keys + ["vendor_spend"], ascending=[True, True, True, False])
    v["vendor_rank"] = v.groupby(keys, dropna=False).cumcount() + 1
    return v


def payment_completion_check(exp: pd.DataFrame, completions: pd.DataFrame) -> pd.DataFrame:
    keys = ["mp_name", "constituency", "state", "ida"]
    e = exp.copy()
    c = completions.copy()
    e["amount_paid"] = pd.to_numeric(e["amount_paid"], errors="coerce").fillna(0)
    c["final_amount"] = pd.to_numeric(c["final_amount"], errors="coerce").fillna(0)
    paid = e.groupby(keys, dropna=False)["amount_paid"].sum().reset_index()
    completed = c.groupby(keys, dropna=False)["final_amount"].sum().reset_index(name="completed_value")
    out = paid.merge(completed, on=keys, how="left")
    out["completed_value"] = out["completed_value"].fillna(0)
    out["payment_completion_difference"] = out["amount_paid"] - out["completed_value"]
    out["payment_completion_difference_pct"] = np.where(
        out["completed_value"] > 0,
        out["payment_completion_difference"] / out["completed_value"] * 100,
        np.nan,
    )
    out["payment_completion_flag"] = (
        (out["payment_completion_difference"] > PAYMENT_MISMATCH_MIN_ABS)
        & (out["payment_completion_difference_pct"] > PAYMENT_MISMATCH_MIN_PCT)
    )
    return out


def summary_reconciliation(exp: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    keys = ["mp_name", "constituency", "state"]
    e = exp.copy(); s = summary.copy()
    e["amount_paid"] = pd.to_numeric(e["amount_paid"], errors="coerce").fillna(0)
    s["summary_total_expenditure"] = pd.to_numeric(s["total_expenditure"], errors="coerce")
    tx = e.groupby(keys, dropna=False)["amount_paid"].sum().reset_index(name="transaction_total_expenditure")
    out = s[keys + ["summary_total_expenditure"]].merge(tx, on=keys, how="left")
    out["transaction_total_expenditure"] = out["transaction_total_expenditure"].fillna(0)
    out["reconciliation_difference"] = out["transaction_total_expenditure"] - out["summary_total_expenditure"]
    out["reconciliation_difference_pct"] = np.where(
        out["summary_total_expenditure"].abs() > 0,
        out["reconciliation_difference"] / out["summary_total_expenditure"].abs() * 100,
        np.nan,
    )
    # This is a data reconciliation indicator, not a fraud flag.
    out["reconciliation_flag"] = out["reconciliation_difference_pct"].abs() > 10
    return out


def build_mp_indicators(exp: pd.DataFrame, completions: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    keys = ["mp_name", "constituency", "state"]
    vc = vendor_concentration(exp)
    top = vc[vc["vendor_rank"] == 1].rename(columns={
        "vendor_name": "top_vendor",
        "vendor_spend": "top_vendor_spend",
        "vendor_share_pct": "top_vendor_share_pct",
    })
    pc = payment_completion_check(exp, completions)
    pc_mp = pc.groupby(keys, dropna=False).agg(
        total_paid=("amount_paid", "sum"),
        total_completed_value=("completed_value", "sum"),
        payment_mismatch_groups=("payment_completion_flag", "sum"),
        max_payment_completion_difference_pct=("payment_completion_difference_pct", "max"),
    ).reset_index()
    rec = summary_reconciliation(exp, summary).drop(columns=["summary_total_expenditure"], errors="ignore")
    out = top[keys + ["top_vendor", "top_vendor_spend", "top_vendor_share_pct"]].merge(pc_mp, on=keys, how="outer").merge(rec, on=keys, how="outer")
    out["vendor_concentration_flag"] = out["top_vendor_share_pct"].fillna(0) >= VENDOR_CONCENTRATION_FLAG_PCT
    out["payment_completion_flag"] = out["payment_mismatch_groups"].fillna(0) > 0
    return out
