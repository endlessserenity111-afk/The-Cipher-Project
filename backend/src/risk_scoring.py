import numpy as np
import pandas as pd
from config import HIGH_RISK, MEDIUM_RISK, VENDOR_HIGH_PCT


def _clip(x, lo=0.0, hi=100.0):
    try:
        value = float(x)
    except (TypeError, ValueError):
        value = 0.0
    if not np.isfinite(value):
        value = 0.0
    return max(lo, min(hi, value))


def _num(value, default=0.0):
    try:
        x = float(value)
    except (TypeError, ValueError):
        return default
    return default if not np.isfinite(x) else x


def score_projects(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    scores, levels, reasons = [], [], []
    for _, r in out.iterrows():
        s = 0.0; ev = []
        over = _num(pd.to_numeric(r.get("positive_amount_difference_pct", 0), errors="coerce"))
        dur = _num(pd.to_numeric(r.get("days_to_completion", 0), errors="coerce"))
        cost_pct = _num(pd.to_numeric(r.get("cost_percentile", 0), errors="coerce"))
        dur_pct = _num(pd.to_numeric(r.get("duration_percentile", 0), errors="coerce"))
        dur_ratio = _num(pd.to_numeric(r.get("duration_ratio_to_peer_median", 0), errors="coerce"))

        if over >= 50:
            s += 18; ev.append(f"Final amount is {over:.1f}% above recommended amount")
        elif over >= 25:
            s += 10; ev.append(f"Final amount is {over:.1f}% above recommended amount")
        if bool(r.get("amount_difference_pct_iqr_flag")):
            s += 8; ev.append("Positive cost deviation is an upper-IQR outlier")
        if cost_pct >= 95:
            s += 12; ev.append(f"Cost deviation is at about the {cost_pct:.0f}th peer percentile")

        if dur >= 540:
            s += 14; ev.append(f"Long recommendation-to-completion timeline ({dur:.0f} days)")
        elif dur >= 360:
            s += 8; ev.append(f"Long recommendation-to-completion timeline ({dur:.0f} days)")
        if bool(r.get("days_to_completion_iqr_flag")):
            s += 7; ev.append("Completion duration is an upper-IQR outlier")
        if dur_pct >= 95:
            s += 10; ev.append(f"Duration is at about the {dur_pct:.0f}th peer percentile")
        if dur_ratio >= 2:
            s += 8; ev.append(f"Duration is about {dur_ratio:.1f}x the peer median")
        if bool(r.get("ml_anomaly_flag")):
            s += 15; ev.append("Isolation Forest detected an unusual multi-feature profile")

        tier = str(r.get("match_tier", "Unmatched"))
        if tier == "Tier 2":
            s *= 0.85
            ev.append("Project evidence comes from a provisional Tier 2 linkage")
        elif tier == "Unmatched":
            # Normally excluded from project scoring, but fail safely.
            s *= 0.60
            ev.append("Project linkage is not verified")

        s = _clip(s)
        level = "HIGH" if s >= HIGH_RISK else "MEDIUM" if s >= MEDIUM_RISK else "LOW"
        if not ev:
            ev.append("No strong project-level anomaly indicators triggered")
        scores.append(round(s, 2)); levels.append(level); reasons.append(" | ".join(ev))

    out["risk_score"] = scores
    out["risk_level"] = levels
    out["risk_reasons"] = reasons
    out["risk_is_assessment"] = True
    return out


def score_mp_indicators(mp: pd.DataFrame) -> pd.DataFrame:
    out = mp.copy(); scores=[]; levels=[]; reasons=[]
    for _, r in out.iterrows():
        s=0.0; ev=[]
        share=_num(pd.to_numeric(r.get("top_vendor_share_pct",0), errors="coerce"))
        mismatch=int(_num(pd.to_numeric(r.get("payment_mismatch_groups",0), errors="coerce")))
        max_diff=_num(pd.to_numeric(r.get("max_payment_completion_difference_pct",0), errors="coerce"))
        recon_flag=bool(r.get("reconciliation_flag", False))
        if share >= VENDOR_HIGH_PCT:
            s += 35; ev.append(f"Top vendor receives {share:.1f}% of recorded expenditure")
        elif share >= 35:
            s += 20; ev.append(f"Top vendor receives {share:.1f}% of recorded expenditure")
        if mismatch > 0:
            s += 30; ev.append(f"{mismatch} MP/IDA payment-completion mismatch group(s)")
        if max_diff >= 50:
            s += 25; ev.append(f"Maximum payment-completion difference is {max_diff:.1f}%")
        if recon_flag:
            s += 10; ev.append("Transaction total differs materially from MP-summary expenditure")
        s=_clip(s)
        lvl="HIGH" if s>=HIGH_RISK else "MEDIUM" if s>=MEDIUM_RISK else "LOW"
        if not ev: ev.append("No strong MP-level financial indicator triggered")
        scores.append(round(s,2)); levels.append(lvl); reasons.append(" | ".join(ev))
    out["mp_risk_score"] = scores; out["mp_risk_level"] = levels; out["mp_risk_reasons"] = reasons
    out["risk_is_assessment"] = True
    return out
