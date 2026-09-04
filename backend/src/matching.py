from collections import defaultdict
import re
import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process
from config import (
    TIER1_THRESHOLD, TIER2_THRESHOLD, MIN_MARGIN_TIER1, MIN_MARGIN_TIER2,
    MAX_CANDIDATES_PER_REC, DATE_WINDOW_DAYS, TIER1_DESC_FLOOR,
    TIER2_DESC_FLOOR, STRONG_CONTEXT_THRESHOLD, MAX_BLOCK_SIZE_FOR_FUZZY,
    PENALTY_IDA_MISMATCH, PENALTY_CATEGORY_MISMATCH, PENALTY_ENTITY_MISMATCH,
    PENALTY_WEAK_ANCHORS,
)

STOP_WORDS={
    'construction','providing','development','improvement','work','works','road','roads','village','at','of','to','from','in','the','and','for','near','under','with','gp','mandal','district','building','installation','community','public','facility','street','system','provision','creation','developmental','strengthening','ward','house'
}

def _ratio(a,b):
    if not a or not b:return 0.0
    return float(fuzz.token_set_ratio(str(a),str(b)))

def _amount_similarity(a,b):
    try:a,b=float(a),float(b)
    except (TypeError,ValueError):return 0.0
    if not np.isfinite(a) or not np.isfinite(b) or a<=0 or b<=0:return 0.0
    return 100.0*min(a,b)/max(a,b)

def _timeline_score(rd,cd):
    if pd.isna(rd) or pd.isna(cd):return 45.0
    d=(cd-rd).days
    if 0<=d<=DATE_WINDOW_DAYS:return max(20.0,100.0-45.0*d/DATE_WINDOW_DAYS)
    if -30<=d<0:return 10.0
    return 0.0

def _tokens(s):return set(re.findall(r'[a-z0-9]+',str(s or '').lower()))

def _anchor_overlap(a,b):
    aa=_tokens(a)-STOP_WORDS; bb=_tokens(b)-STOP_WORDS
    if not aa or not bb:return 0.0
    return 100.0*len(aa&bb)/max(1,min(len(aa),len(bb)))

def _score(rec,comp):
    desc=_ratio(rec.get('work_norm',''),comp.get('work_norm',''))
    mp=_ratio(rec.get('mp_canonical',rec.get('mp_norm','')),comp.get('mp_canonical',comp.get('mp_norm','')))
    constituency=_ratio(rec.get('constituency_canonical',rec.get('constituency_norm','')),comp.get('constituency_canonical',comp.get('constituency_norm','')))
    state=_ratio(rec.get('state_norm',''),comp.get('state_norm',''))
    ida=_ratio(rec.get('ida_norm',''),comp.get('ida_norm',''))
    category=_ratio(rec.get('category_norm',''),comp.get('category_norm',''))
    amount=_amount_similarity(rec.get('recommended_amount'),comp.get('final_amount'))
    timeline=_timeline_score(rec.get('recommendation_date'),comp.get('completed_date'))
    anchors=_anchor_overlap(rec.get('work_norm',''),comp.get('work_norm',''))
    score=.66*desc+.10*mp+.09*constituency+.04*state+.03*ida+.03*category+.03*amount+.02*timeline
    warnings=[]
    pairs=[('mp_canonical_key','mp_canonical_key','different MP',PENALTY_ENTITY_MISMATCH),('state_norm_key','state_norm_key','different state',PENALTY_ENTITY_MISMATCH),('constituency_canonical_key','constituency_canonical_key','different constituency',PENALTY_ENTITY_MISMATCH),('ida_key','ida_key','different IDA',PENALTY_IDA_MISMATCH),('category_norm_key','category_norm_key','different category',PENALTY_CATEGORY_MISMATCH)]
    for a,b,w,p in pairs:
        if rec.get(a) and comp.get(b) and rec.get(a)!=comp.get(b):score-=p;warnings.append(w)
    if anchors<30 and desc<95:score-=PENALTY_WEAK_ANCHORS;warnings.append('weak shared project tokens')
    ev={'description_similarity':round(desc,2),'mp_similarity':round(mp,2),'constituency_similarity':round(constituency,2),'state_similarity':round(state,2),'ida_similarity':round(ida,2),'category_similarity':round(category,2),'amount_similarity':round(amount,2),'timeline_match_score':round(timeline,2),'project_token_overlap':round(anchors,2)}
    return max(0.0,float(score)),ev,warnings

def _eligible_date(r,c):
    rd=r.get('recommendation_date');cd=c.get('completed_date')
    if pd.isna(rd) or pd.isna(cd):return True
    d=(cd-rd).days
    return -30<=d<=DATE_WINDOW_DAYS

def _tier(score,margin,ev,warnings):
    strong=ev['mp_similarity']>=STRONG_CONTEXT_THRESHOLD and ev['state_similarity']>=STRONG_CONTEXT_THRESHOLD and ev['constituency_similarity']>=STRONG_CONTEXT_THRESHOLD
    hard=any(w in warnings for w in ('different MP','different state','different constituency'))
    weak=ev['description_similarity']<TIER2_DESC_FLOOR or ev['project_token_overlap']<25
    if score>=TIER1_THRESHOLD and margin>=MIN_MARGIN_TIER1 and ev['description_similarity']>=TIER1_DESC_FLOOR and strong and not hard and not weak:
        if 'different IDA' in warnings and ev['description_similarity']<96:return 'Unmatched','Unmatched'
        if 'different category' in warnings and ev['description_similarity']<95:return 'Unmatched','Unmatched'
        return 'Tier 1','Verified'
    if score>=TIER2_THRESHOLD and margin>=MIN_MARGIN_TIER2 and ev['description_similarity']>=TIER2_DESC_FLOOR and strong and not hard and not weak:
        if 'different IDA' in warnings and ev['description_similarity']<90:return 'Unmatched','Unmatched'
        return 'Tier 2','Provisional'
    return 'Unmatched','Unmatched'

def _build_indices(comp):
    entity=defaultdict(list); sc=defaultdict(list); state=defaultdict(list); work_ids=defaultdict(list); exact=defaultdict(list); token_index=defaultdict(list)
    for ci,row in comp.iterrows():
        d=row.to_dict();ek=(d.get('state_norm_key',''),d.get('constituency_canonical_key',''),d.get('mp_canonical_key',''));sk=(d.get('state_norm_key',''),d.get('constituency_canonical_key',''))
        entity[ek].append(ci);sc[sk].append(ci);state[d.get('state_norm_key','')].append(ci)
        wid=str(d.get('work_id_key','') or '');
        if wid:work_ids[wid].append(ci)
        w=str(d.get('work_norm','') or '')
        if w: exact[w].append(ci)
        for tok in (_tokens(w)-STOP_WORDS):
            token_index[tok].append(ci)
    # Most frequent token lists can create huge candidate sets; keep rare/common information.
    token_freq={k:len(v) for k,v in token_index.items()}
    return entity,sc,state,work_ids,exact,token_index,token_freq

def _token_candidates(work,token_index,token_freq,limit_tokens=8,max_candidates=2500):
    toks=[t for t in (_tokens(work)-STOP_WORDS) if t in token_index]
    toks.sort(key=lambda t:token_freq[t])
    chosen=toks[:limit_tokens]
    pool=[];seen=set()
    for tok in chosen:
        for ci in token_index[tok]:
            if ci not in seen:
                seen.add(ci);pool.append(ci)
                if len(pool)>=max_candidates:return pool
    return pool

def match_records(rec_df,comp_df):
    rec=rec_df.reset_index(drop=True).copy();comp=comp_df.reset_index(drop=True).copy()
    entity,sc,state,work_ids,exact,token_index,token_freq=_build_indices(comp)
    results=[]
    for ri,r in rec.iterrows():
        rd=r.to_dict();work=str(rd.get('work_norm','') or '')
        base={'recommendation_index':ri,'completion_index':-1,'match_score':0.0,'match_tier':'Unmatched','match_confidence':'Unmatched','score_margin':0.0,'best_candidate_index':-1,'best_candidate_score':0.0,'best_candidate_tier':'Unmatched','match_reason':''}
        if not work:base['match_reason']='Missing work description.';results.append(base);continue
        ek=(rd.get('state_norm_key',''),rd.get('constituency_canonical_key',''),rd.get('mp_canonical_key',''));sk=(rd.get('state_norm_key',''),rd.get('constituency_canonical_key',''));state_key=rd.get('state_norm_key','')
        entity_candidates=entity.get(ek,[]);sc_candidates=sc.get(sk,[])
        scored=[]
        # 1) Exact normalized work description within same entity context.
        for ci in exact.get(work,[]):
            if ci in set(entity_candidates):
                cd=comp.iloc[ci].to_dict()
                if _eligible_date(rd,cd): scored.append((*_score(rd,cd),'exact normalized description',ci))
        # 2) Corroborated Work ID.
        wid=str(rd.get('work_id_key','') or '')
        for ci in work_ids.get(wid,[])[:MAX_CANDIDATES_PER_REC] if wid else []:
            cd=comp.iloc[ci].to_dict()
            if _eligible_date(rd,cd) and _ratio(work,cd.get('work_norm',''))>=80 and _ratio(rd.get('mp_norm',''),cd.get('mp_norm',''))>=95 and _ratio(rd.get('state_norm',''),cd.get('state_norm',''))>=95:
                scored.append((*_score(rd,cd),'corroborated Work ID',ci))
        # 3) Retrieval: first from the exact entity block, otherwise token index, then same state.
        if not scored:
            shortlist=[]; source='fuzzy token retrieval'
            if entity_candidates and len(entity_candidates)<=MAX_BLOCK_SIZE_FOR_FUZZY:
                choices=[comp.iloc[i].get('work_norm','') for i in entity_candidates]
                hits=process.extract(work,choices,scorer=fuzz.token_set_ratio,limit=MAX_CANDIDATES_PER_REC,score_cutoff=55)
                shortlist=[entity_candidates[pos] for _,_,pos in hits]; source='blocked fuzzy retrieval'
            else:
                shortlist=_token_candidates(work,token_index,token_freq,max_candidates=1200)
                # Prefer same state+constituency, then same state among retrieved candidates.
                scset=set(sc_candidates); filt=[ci for ci in shortlist if ci in scset]
                if filt:shortlist=filt
                else:
                    stset=set(state.get(state_key,[]));filt=[ci for ci in shortlist if ci in stset]
                    if filt:shortlist=filt
                shortlist=shortlist[:MAX_CANDIDATES_PER_REC]
            for ci in shortlist:
                cd=comp.iloc[int(ci)].to_dict()
                if not _eligible_date(rd,cd):continue
                scored.append((*_score(rd,cd),source,int(ci)))
        if not scored:
            base['match_reason']='No candidate survived description/date screening.'
            best_pool=_token_candidates(work,token_index,token_freq,max_candidates=300)
            if best_pool:
                choices=[comp.iloc[i].get('work_norm','') for i in best_pool]
                hit=process.extractOne(work,choices,scorer=fuzz.token_set_ratio)
                if hit:
                    _,_,pos=hit;ci=best_pool[pos];s,ev,w=_score(rd,comp.iloc[ci].to_dict());base.update({'best_candidate_index':int(ci),'best_candidate_score':round(s,3),'match_reason':'Best candidate did not reach a match tier; '+', '.join(f'{k}={v:.1f}' for k,v in ev.items())})
            results.append(base);continue
        byci={}
        for s,ev,w,source,ci in scored:
            if ci not in byci or s>byci[ci][0]:byci[ci]=(s,ev,w,source,ci)
        ranked=sorted(byci.values(),key=lambda x:x[0],reverse=True);best=ranked[0];second=ranked[1][0] if len(ranked)>1 else 0.0;margin=best[0]-second;tier,conf=_tier(best[0],margin,best[1],best[2])
        reason=(f'{best[3]}; description={best[1]["description_similarity"]:.1f}; mp={best[1]["mp_similarity"]:.1f}; constituency={best[1]["constituency_similarity"]:.1f}; state={best[1]["state_similarity"]:.1f}; ida={best[1]["ida_similarity"]:.1f}; category={best[1]["category_similarity"]:.1f}; amount={best[1]["amount_similarity"]:.1f}; timeline={best[1]["timeline_match_score"]:.1f}; token_overlap={best[1]["project_token_overlap"]:.1f}')
        if best[2]:reason+='; warnings='+', '.join(best[2])
        base.update({'completion_index':int(best[4]) if tier!='Unmatched' else -1,'match_score':round(best[0],3) if tier!='Unmatched' else 0.0,'match_tier':tier,'match_confidence':conf,'score_margin':round(margin,3),'best_candidate_index':int(best[4]),'best_candidate_score':round(best[0],3),'best_candidate_tier':tier,'match_reason':reason})
        results.append(base)
    out=pd.DataFrame(results)
    accepted=out[out.completion_index>=0]
    if not accepted.empty:
        winners=accepted.sort_values(['completion_index','match_score'],ascending=[True,False]).drop_duplicates('completion_index');keep=set(zip(winners.recommendation_index,winners.completion_index))
        for idx,row in out.iterrows():
            if row.completion_index>=0 and (int(row.recommendation_index),int(row.completion_index)) not in keep:
                out.loc[idx,['completion_index','match_score','match_tier','match_confidence']]=[-1,0.0,'Unmatched','Unmatched'];out.loc[idx,'match_reason']='Candidate was already assigned to a stronger recommendation match.'
    return out
