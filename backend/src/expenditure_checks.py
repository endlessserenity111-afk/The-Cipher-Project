import numpy as np
import pandas as pd


def vendor_concentration(exp: pd.DataFrame) -> pd.DataFrame:
    e = exp.copy()
    e["amount_paid"] = pd.to_numeric(e["amount_paid"], errors="coerce").fillna(0)
    group = e.groupby(["mp_name", "constituency", "state"], dropna=False)
    total = group["amount_paid"].sum().rename("mp_total_spend")
    ev = e.merge(total, on=["mp_name", "constituency", "state"], how="left")
    v = ev.groupby(["mp_name", "constituency", "state", "vendor_name"], dropna=False)["amount_paid"].sum().reset_index(name="vendor_spend")
    v = v.merge(total.reset_index(), on=["mp_name", "constituency", "state"], how="left")
    v["vendor_share_pct"] = np.where(v["mp_total_spend"] > 0, v["vendor_spend"] / v["mp_total_spend"] * 100, np.nan)
    v = v.sort_values(["mp_name","vendor_spend"], ascending=[True,False])
    v["vendor_rank"] = v.groupby(["mp_name", "constituency", "state"]).cumcount() + 1
    return v


def payment_completion_check(project_features: pd.DataFrame, exp: pd.DataFrame) -> pd.DataFrame:
    # No Work ID exists in expenditures, so aggregate at MP + IDA as a deliberately separate evidence layer.
    e = exp.copy()
    e["amount_paid"] = pd.to_numeric(e["amount_paid"], errors="coerce").fillna(0)
    paid = e.groupby(["mp_name", "constituency", "state", "ida"], dropna=False)["amount_paid"].sum().reset_index()
    completed = project_features.copy()
    completed["final_amount"] = pd.to_numeric(completed["final_amount"], errors="coerce").fillna(0)
    comp = completed.groupby(["mp_name", "constituency", "state", "ida"], dropna=False)["final_amount"].sum().reset_index(name="completed_value")
    out = paid.merge(comp, on=["mp_name", "constituency", "state", "ida"], how="left")
    out["completed_value"] = out["completed_value"].fillna(0)
    out["payment_completion_difference"] = out["amount_paid"] - out["completed_value"]
    out["payment_completion_difference_pct"] = np.where(
        out["completed_value"] > 0,
        out["payment_completion_difference"] / out["completed_value"] * 100,
        np.nan,
    )
    out["payment_completion_flag"] = (
        (out["payment_completion_difference"] > 500000) &
        (out["payment_completion_difference_pct"] > 25)
    )
    return out


def build_mp_indicators(exp: pd.DataFrame, project_features: pd.DataFrame) -> pd.DataFrame:
    vc = vendor_concentration(exp)
    top_vendor = vc[vc["vendor_rank"] == 1].copy()
    top_vendor = top_vendor.rename(columns={
        "vendor_name": "top_vendor", "vendor_spend": "top_vendor_spend", "vendor_share_pct": "top_vendor_share_pct"
    })
    pc = payment_completion_check(project_features, exp)
    # Roll payment mismatch from MP+IDA to MP level using max mismatch percentage and total absolute mismatch.
    mp_pc = pc.groupby(["mp_name","constituency","state"], dropna=False).agg(
        total_paid=("amount_paid","sum"),
        total_completed_value=("completed_value","sum"),
        max_payment_completion_difference_pct=("payment_completion_difference_pct","max"),
        payment_mismatch_groups=("payment_completion_flag","sum"),
    ).reset_index()
    mp = top_vendor[["mp_name","constituency","state","top_vendor","top_vendor_spend","top_vendor_share_pct"]].merge(
        mp_pc, on=["mp_name","constituency","state"], how="outer"
    )
    mp["vendor_concentration_flag"] = mp["top_vendor_share_pct"].fillna(0) >= 35.0
    mp["payment_completion_flag"] = mp["payment_mismatch_groups"].fillna(0) > 0
    return mp
