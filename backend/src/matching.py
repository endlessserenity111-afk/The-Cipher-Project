from collections import defaultdict
import re
import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process
from config import *

def _ratio(a,b):
    if not a or not b: return 0.0
    return float(fuzz.token_set_ratio(str(a), str(b)))

def _amount(a,b):
    try: a=float(a); b=float(b)
    except: return 0.0
    if a<=0 or b<=0: return 0.0
    return 100.0*min(a,b)/max(a,b)

def _date_score(a,b):
    if pd.isna(a) or pd.isna(b): return 45.0
    d=(b-a).days
    if 0<=d<=DATE_WINDOW_DAYS: return max(20.0,100.0-50.0*d/DATE_WINDOW_DAYS)
    if -30<=d<0: return 10.0
    return 0.0

def _tokens(s): return set(re.findall(r'[a-z0-9]+', str(s or '').lower()))

def _anchor_overlap(a,b):
    stop={'construction','providing','development','improvement','work','works','road','roads','village','at','of','to','from','in','the','and','for','near','under','with','gp','mandal','district','building','installation','community','public','facility','street','system'}
    aa=_tokens(a)-stop; bb=_tokens(b)-stop
    if not aa or not bb: return 0.0
    return 100.0*len(aa&bb)/max(1,min(len(aa),len(bb)))

def _score(rec, comp):
    desc=_ratio(rec.get('work_norm',''),comp.get('work_norm',''))
    mp=_ratio(rec.get('mp_norm',''),comp.get('mp_norm',''))
    con=_ratio(rec.get('constituency_norm',''),comp.get('constituency_norm',''))
    state=_ratio(rec.get('state_norm',''),comp.get('state_norm',''))
    ida=_ratio(rec.get('ida_norm',''),comp.get('ida_norm',''))
    cat=_ratio(rec.get('category_norm',''),comp.get('category_norm',''))
    amt=_amount(rec.get('recommended_amount'),comp.get('final_amount'))
    date=_date_score(rec.get('recommendation_date'),comp.get('completed_date'))
    anchors=_anchor_overlap(rec.get('work_norm',''),comp.get('work_norm',''))
    score=.55*desc+.10*mp+.10*con+.05*state+.05*ida+.05*cat+.05*amt+.05*date
    warnings=[]
    if rec.get('ida_key') and comp.get('ida_key') and rec['ida_key']!=comp['ida_key']:
        score-=CONTRADICTION_IDA_PENALTY; warnings.append('different IDA')
    if rec.get('category_key') and comp.get('category_key') and rec['category_key']!=comp['category_key']:
        score-=CONTRADICTION_CATEGORY_PENALTY; warnings.append('different category')
    if anchors<30 and desc<95:
        score-=4.0; warnings.append('weak shared project/location tokens')
    ev={'description_similarity':round(desc,2),'mp_similarity':round(mp,2),'constituency_similarity':round(con,2),'state_similarity':round(state,2),'ida_similarity':round(ida,2),'category_similarity':round(cat,2),'amount_similarity':round(amt,2),'date_score':round(date,2),'project_token_overlap':round(anchors,2)}
    return max(0.0,float(score)),ev,warnings

def _tier(score, margin, ev, warnings):
    context=ev['mp_similarity']>=STRONG_CONTEXT_THRESHOLD and ev['state_similarity']>=STRONG_CONTEXT_THRESHOLD and ev['constituency_similarity']>=STRONG_CONTEXT_THRESHOLD
    if score>=TIER1_THRESHOLD and margin>=MIN_MARGIN and ev['description_similarity']>=TIER1_DESC_FLOOR and context and len(warnings)<=1:
        # IDA disagreement is tolerated only when description evidence is extremely strong.
        if 'different IDA' in warnings and ev['description_similarity']<95: return 'Unmatched','Unmatched'
        return 'Tier 1','Verified'
    if score>=TIER2_THRESHOLD and margin>=MIN_MARGIN/2 and ev['description_similarity']>=TIER2_DESC_FLOOR and context and len(warnings)<=1:
        if 'different IDA' in warnings and ev['description_similarity']<90: return 'Unmatched','Unmatched'
        return 'Tier 2','Provisional'
    return 'Unmatched','Unmatched'

def match_records(rec_df, comp_df):
    rec=rec_df.reset_index(drop=True).copy(); comp=comp_df.reset_index(drop=True).copy()
    blocks=defaultdict(list); state_blocks=defaultdict(list); ids=defaultdict(list)
    for ci,c in comp.iterrows():
        st=c.get('state_norm','') or ''; co=c.get('constituency_norm','') or ''; mp=c.get('mp_canonical',c.get('mp_norm','')) or ''; w=c.get('work_norm','') or ''
        blocks[(st,co,mp)].append((ci,w)); state_blocks[(st,co)].append((ci,w))
        wid=str(c.get('work_id_key','') or '')
        if wid: ids[wid].append(ci)
    rows=[]
    for ri,r in rec.iterrows():
        rd=r.to_dict(); st=rd.get('state_norm','') or ''; co=rd.get('constituency_norm','') or ''; mp=rd.get('mp_canonical',rd.get('mp_norm','')) or ''; work=rd.get('work_norm','') or ''
        if not work:
            rows.append({'recommendation_index':ri,'completion_index':-1,'match_score':0.0,'match_tier':'Unmatched','match_confidence':'Unmatched','score_margin':0.0,'match_reason':'Missing work description.'}); continue
        choices=blocks.get((st,co,mp),[]) or state_blocks.get((st,co),[])
        if not choices:
            rows.append({'recommendation_index':ri,'completion_index':-1,'match_score':0.0,'match_tier':'Unmatched','match_confidence':'Unmatched','score_margin':0.0,'match_reason':'No compatible geographic/entity candidate block.'}); continue
        candidates=[]
        # Corroborated ID is considered first but never trusted alone.
        wid=str(rd.get('work_id_key','') or '')
        for ci in ids.get(wid,[]) if wid else []:
            c=comp.iloc[ci]
            if _ratio(rd.get('mp_norm',''),c.get('mp_norm',''))>=95 and _ratio(rd.get('state_norm',''),c.get('state_norm',''))>=95:
                s,e,w=_score(rd,c); candidates.append((s,ci,e,w,'corroborated Work ID'))
        if not candidates:
            hits=process.extract(work,[x[1] for x in choices],scorer=fuzz.token_set_ratio,limit=MAX_CANDIDATES_PER_REC,score_cutoff=45)
            for _,_,pos in hits:
                ci=choices[pos][0]; c=comp.iloc[ci]
                if not pd.isna(rd.get('recommendation_date')) and not pd.isna(c.get('completed_date')):
                    delta=(c.get('completed_date')-rd.get('recommendation_date')).days
                    if delta<-30 or delta>DATE_WINDOW_DAYS: continue
                s,e,w=_score(rd,c); candidates.append((s,ci,e,w,'fuzzy retrieval'))
        if not candidates:
            rows.append({'recommendation_index':ri,'completion_index':-1,'match_score':0.0,'match_tier':'Unmatched','match_confidence':'Unmatched','score_margin':0.0,'match_reason':'No candidate passed description/date screening.'}); continue
        byci={}
        for item in candidates: byci[item[1]]=max(byci.get(item[1],item),item,key=lambda z:z[0])
        ranked=sorted(byci.values(),key=lambda z:z[0],reverse=True); best=ranked[0]; second=ranked[1][0] if len(ranked)>1 else 0.0; margin=best[0]-second
        tier,conf=_tier(best[0],margin,best[2],best[3])
        reason=f"{best[4]}; description={best[2]['description_similarity']:.1f}; mp={best[2]['mp_similarity']:.1f}; constituency={best[2]['constituency_similarity']:.1f}; state={best[2]['state_similarity']:.1f}; ida={best[2]['ida_similarity']:.1f}; category={best[2]['category_similarity']:.1f}; amount={best[2]['amount_similarity']:.1f}; date={best[2]['date_score']:.1f}; token_overlap={best[2]['project_token_overlap']:.1f}"
        if best[3]: reason+='; warnings='+', '.join(best[3])
        rows.append({'recommendation_index':ri,'completion_index':best[1] if tier!='Unmatched' else -1,'match_score':round(best[0],3) if tier!='Unmatched' else 0.0,'match_tier':tier,'match_confidence':conf,'score_margin':round(margin,3),'match_reason':reason})
    out=pd.DataFrame(rows)
    valid=out[out.completion_index>=0]
    if not valid.empty:
        winners=valid.sort_values(['completion_index','match_score'],ascending=[True,False]).drop_duplicates('completion_index')
        keep=set(zip(winners.recommendation_index,winners.completion_index)); pairs=list(zip(out.recommendation_index,out.completion_index))
        collision=(out.completion_index>=0) & ~pd.Series(pairs,index=out.index).isin(keep)
        out.loc[collision,['completion_index','match_score','match_tier','match_confidence']]=[-1,0.0,'Unmatched','Unmatched']
        out.loc[collision,'match_reason']='Candidate was already assigned to a stronger recommendation match.'
    return out
