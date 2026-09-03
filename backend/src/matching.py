from collections import defaultdict
from typing import Tuple
import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

from config import TIER1_THRESHOLD, TIER2_THRESHOLD, MIN_MARGIN, MAX_CANDIDATES_PER_REC, DATE_WINDOW_DAYS


def _safe_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return float(fuzz.token_set_ratio(a, b))


def _amount_similarity(a, b) -> float:
    try:
        a = float(a); b = float(b)
    except Exception:
        return 0.0
    if a <= 0 or b <= 0:
        return 0.0
    return float(min(a, b) / max(a, b) * 100.0)


def _date_score(rec_date, comp_date) -> float:
    if pd.isna(rec_date) or pd.isna(comp_date):
        return 45.0
    days = (comp_date - rec_date).days
    if 0 <= days <= DATE_WINDOW_DAYS:
        return max(20.0, 100.0 - days / DATE_WINDOW_DAYS * 50.0)
    if -30 <= days < 0:
        return 20.0
    return 0.0


def _candidate_score(rec, comp) -> Tuple[float, dict]:
    desc = _safe_ratio(rec.get("work_norm", ""), comp.get("work_norm", ""))
    mp = _safe_ratio(rec.get("mp_norm", ""), comp.get("mp_norm", ""))
    constituency = _safe_ratio(rec.get("constituency_norm", ""), comp.get("constituency_norm", ""))
    state = _safe_ratio(rec.get("state_norm", ""), comp.get("state_norm", ""))
    ida = _safe_ratio(rec.get("ida_norm", ""), comp.get("ida_norm", ""))
    category = _safe_ratio(rec.get("category_norm", ""), comp.get("category_norm", ""))
    amount = _amount_similarity(rec.get("recommended_amount", np.nan), comp.get("final_amount", np.nan))
    date = _date_score(rec.get("recommendation_date"), comp.get("completed_date"))
    score = 0.42*desc + 0.16*mp + 0.14*constituency + 0.08*state + 0.07*ida + 0.05*category + 0.05*amount + 0.03*date
    evidence = {
        "description_similarity": round(desc,2), "mp_similarity": round(mp,2),
        "constituency_similarity": round(constituency,2), "state_similarity": round(state,2),
        "ida_similarity": round(ida,2), "category_similarity": round(category,2),
        "amount_similarity": round(amount,2), "date_score": round(date,2)
    }
    return float(score), evidence


def _pick_exact_candidate(rec, indices, comp):
    best = None
    for ci in indices:
        c = comp.iloc[ci]
        score, ev = _candidate_score(rec, c)
        # Exact description + entity block is strong enough for Tier 1.
        tie = _amount_similarity(rec.get("recommended_amount", np.nan), c.get("final_amount", np.nan))
        key = (score, tie)
        if best is None or key > best[0]:
            best = (key, ci, score, ev)
    return None if best is None else best[1:]


def match_records(rec_df: pd.DataFrame, comp_df: pd.DataFrame) -> pd.DataFrame:
    rec = rec_df.reset_index(drop=True).copy()
    comp = comp_df.reset_index(drop=True).copy()

    # Fast lookup structures. Most real records share state + constituency + MP; only
    # unresolved records need fuzzy fallback.
    entity_blocks = defaultdict(list)
    entity_desc = defaultdict(list)
    state_const_blocks = defaultdict(list)
    for ci, row in comp.iterrows():
        state = row.get("state_norm", "") or ""
        con = row.get("constituency_norm", "") or ""
        mp = row.get("mp_canonical", row.get("mp_norm", "")) or ""
        work = row.get("work_norm", "") or ""
        entity_blocks[(state, con, mp)].append((ci, work))
        entity_desc[(state, con, mp, work)].append(ci)
        state_const_blocks[(state, con)].append((ci, work))

    results=[]
    for ridx, row in rec.iterrows():
        r=row.to_dict()
        state=r.get("state_norm", "") or ""; con=r.get("constituency_norm", "") or ""; mp=r.get("mp_canonical", r.get("mp_norm", "")) or ""; work=r.get("work_norm", "") or ""
        exact_list=entity_desc.get((state,con,mp,work), []) if work else []
        if exact_list:
            picked=_pick_exact_candidate(r, exact_list, comp)
            ci,score,ev=picked
            results.append({"recommendation_index":ridx,"completion_index":int(ci),"match_score":round(score,3),"match_tier":"Tier 1","match_confidence":"Verified","score_margin":100.0,"match_reason":"Exact normalized work description within matching state/constituency/MP entity block."})
            continue

        choices=entity_blocks.get((state,con,mp), [])
        block_type="state+constituency+MP"
        if not choices:
            choices=state_const_blocks.get((state,con), [])
            block_type="state+constituency"
        if not choices and state:
            # No fuzzy global fallback: a weak global match is more dangerous than unmatched.
            results.append({"recommendation_index":ridx,"completion_index":-1,"match_score":0.0,"match_tier":"Unmatched","match_confidence":"Unmatched","score_margin":0.0,"match_reason":"No compatible geographic/entity candidate block."})
            continue
        if not work:
            results.append({"recommendation_index":ridx,"completion_index":-1,"match_score":0.0,"match_tier":"Unmatched","match_confidence":"Unmatched","score_margin":0.0,"match_reason":"Missing work description; fuzzy matching intentionally skipped."})
            continue

        # RapidFuzz retrieval is done only within a strongly blocked group.
        texts=[x[1] for x in choices]
        hits=process.extract(work,texts,scorer=fuzz.token_set_ratio,limit=MAX_CANDIDATES_PER_REC,score_cutoff=35)
        scored=[]
        for _,_,pos in hits:
            ci=choices[pos][0]; c=comp.iloc[ci]
            if not pd.isna(r.get("recommendation_date")) and not pd.isna(c.get("completed_date")):
                delta=(c.get("completed_date")-r.get("recommendation_date")).days
                if delta < -30 or delta > DATE_WINDOW_DAYS:
                    continue
            s,ev=_candidate_score(r,c); scored.append((s,int(ci),ev))
        scored.sort(reverse=True,key=lambda x:x[0])
        if not scored:
            results.append({"recommendation_index":ridx,"completion_index":-1,"match_score":0.0,"match_tier":"Unmatched","match_confidence":"Unmatched","score_margin":0.0,"match_reason":"No candidate passed description and date screening."})
            continue
        best=scored[0]; second=scored[1][0] if len(scored)>1 else 0.0; margin=best[0]-second
        if best[0]>=TIER1_THRESHOLD and margin>=MIN_MARGIN:
            tier,conf="Tier 1","Verified"
        elif best[0]>=TIER2_THRESHOLD and margin>=MIN_MARGIN/2:
            tier,conf="Tier 2","Provisional"
        else:
            tier,conf="Unmatched","Unmatched"
        results.append({"recommendation_index":ridx,"completion_index":best[1] if tier!="Unmatched" else -1,"match_score":round(best[0],3) if tier!="Unmatched" else 0.0,"match_tier":tier,"match_confidence":conf,"score_margin":round(margin,3),"match_reason":f"Fuzzy description retrieval within {block_type}; " + "; ".join(f"{k}={v}" for k,v in best[2].items() if v>=70)})

    out=pd.DataFrame(results)
    valid=out[out["completion_index"]>=0]
    if not valid.empty:
        best_per_completion=valid.sort_values(["completion_index","match_score"],ascending=[True,False]).drop_duplicates("completion_index")
        keep_pairs=set(zip(best_per_completion["recommendation_index"],best_per_completion["completion_index"]))
        out["_pair"]=list(zip(out["recommendation_index"],out["completion_index"]))
        collision=(out["completion_index"]>=0) & ~out["_pair"].isin(keep_pairs)
        out.loc[collision,["completion_index","match_score","match_tier","match_confidence"]]=[-1,0.0,"Unmatched","Unmatched"]
        out.loc[collision,"match_reason"]="Candidate was already assigned to a stronger recommendation match."
        out=out.drop(columns=["_pair"])
    return out
