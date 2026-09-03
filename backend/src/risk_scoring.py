import numpy as np
import pandas as pd
from config import HIGH_RISK, MEDIUM_RISK


def _clip(x, lo=0, hi=100):
    return max(lo, min(hi, float(x)))


def score_projects(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    reasons_all = []
    scores = []
    levels = []
    for _, r in out.iterrows():
        evidence = []
        score = 0.0
        over = float(r.get("amount_difference_pct", 0) or 0)
        days = float(r.get("days_to_completion", 0) or 0)
        if over >= 50:
            score += 22; evidence.append(f"Final amount {over:.1f}% above recommended amount")
        elif over >= 25:
            score += 12; evidence.append(f"Final amount {over:.1f}% above recommended amount")
        if bool(r.get("amount_difference_pct_iqr_flag", False)):
            score += 10; evidence.append("Cost deviation is an upper-IQR outlier")
        if days >= 540:
            score += 18; evidence.append(f"Very long recommendation-to-completion duration ({days:.0f} days)")
        elif days >= 360:
            score += 10; evidence.append(f"Long recommendation-to-completion duration ({days:.0f} days)")
        if bool(r.get("days_to_completion_iqr_flag", False)):
            score += 8; evidence.append("Completion duration is an upper-IQR outlier")
        if bool(r.get("ml_anomaly_flag", False)):
            score += 20; evidence.append("Isolation Forest detected an unusual project profile")
        tier = str(r.get("match_tier", "Unmatched"))
        match_score = float(r.get("match_score", 0) or 0)
        if tier == "Tier 1":
            score += 5
        elif tier == "Tier 2":
            score *= 0.88
            evidence.append("Evidence derived from a provisional Tier 2 project match")
        else:
            score *= 0.60
        score = _clip(score)
        if score >= HIGH_RISK:
            level = "HIGH"
        elif score >= MEDIUM_RISK:
            level = "MEDIUM"
        else:
            level = "LOW"
        if not evidence:
            evidence.append("No strong project-level anomaly indicators triggered")
        reasons_all.append(" | ".join(evidence))
        scores.append(round(score, 2)); levels.append(level)
    out["risk_score"] = scores
    out["risk_level"] = levels
    out["risk_reasons"] = reasons_all
    out["risk_is_assessment"] = True
    return out


def score_mp_indicators(mp: pd.DataFrame) -> pd.DataFrame:
    out = mp.copy()
    scores=[]; reasons=[]; levels=[]
    for _, r in out.iterrows():
        s=0; ev=[]
        share=float(r.get("top_vendor_share_pct",0) or 0)
        mismatch=int(r.get("payment_mismatch_groups",0) or 0)
        maxdiff=float(r.get("max_payment_completion_difference_pct",0) or 0)
        if share >= 60: s += 35; ev.append(f"Top vendor receives {share:.1f}% of recorded expenditure")
        elif share >= 35: s += 20; ev.append(f"Top vendor receives {share:.1f}% of recorded expenditure")
        if mismatch > 0: s += 30; ev.append(f"{mismatch} MP/IDA payment-completion mismatch group(s)")
        if maxdiff >= 50: s += 25; ev.append(f"Maximum payment-completion mismatch is {maxdiff:.1f}%")
        s=_clip(s)
        lvl="HIGH" if s>=HIGH_RISK else "MEDIUM" if s>=MEDIUM_RISK else "LOW"
        if not ev: ev.append("No strong MP-level financial concentration/mismatch indicator triggered")
        scores.append(s); reasons.append(" | ".join(ev)); levels.append(lvl)
    out["mp_risk_score"] = scores
    out["mp_risk_level"] = levels
    out["mp_risk_reasons"] = reasons
    out["risk_is_assessment"] = True
    return out
