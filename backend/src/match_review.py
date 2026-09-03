from pathlib import Path
import html, re, pandas as pd
REVIEW_COLUMNS=['review_id','match_tier','match_confidence','match_score','score_margin','recommendation_index','completion_index','recommendation_work_id','completion_work_id','recommendation_description','completion_description','recommendation_mp','completion_mp','recommendation_state','completion_state','recommendation_constituency','completion_constituency','recommendation_category','completion_category','recommendation_ida','completion_ida','recommended_amount','final_amount','description_similarity','mp_similarity','constituency_similarity','state_similarity','ida_similarity','category_similarity','amount_similarity','date_score','project_token_overlap','match_reason','human_verdict','human_notes']

def _num(reason,key):
    m=re.search(r'(?:^|; )'+re.escape(key)+r'=([0-9]+(?:\.[0-9]+)?)',str(reason)); return float(m.group(1)) if m else ''

def _sample(df,tier,seed=42):
    x=df[df.match_tier.eq(tier)].copy()
    if x.empty:return x
    parts=[]; used=set()
    for part in [x.sample(n=min(5,len(x)),random_state=seed), None, None]:
        if part is not None: parts.append(part); used.update(part.index)
    rem=x.loc[~x.index.isin(used)]; parts.append(rem.sort_values(['match_score','score_margin']).head(3)); used.update(parts[-1].index)
    rem=x.loc[~x.index.isin(used)]; parts.append(rem.sort_values(['match_score','score_margin'],ascending=[False,False]).head(2))
    return pd.concat(parts).drop_duplicates().reset_index(drop=True)

def _g(row,*names):
    for n in names:
        if n in row.index:return row.get(n,'')
    return ''

def build_review_samples(matches,recommendations,completions,output_dir:Path,seed=42):
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True); rows=[]
    for tier in ['Tier 1','Tier 2']:
        for _,m in _sample(matches,tier,seed).iterrows():
            rr=recommendations.iloc[int(m.recommendation_index)]; cc=completions.iloc[int(m.completion_index)]
            rows.append({'review_id':len(rows)+1,'match_tier':m.match_tier,'match_confidence':m.match_confidence,'match_score':m.match_score,'score_margin':m.score_margin,'recommendation_index':int(m.recommendation_index),'completion_index':int(m.completion_index),'recommendation_work_id':_g(rr,'work_id'),'completion_work_id':_g(cc,'work_id'),'recommendation_description':_g(rr,'work_description'),'completion_description':_g(cc,'work_description'),'recommendation_mp':_g(rr,'mp_name'),'completion_mp':_g(cc,'mp_name'),'recommendation_state':_g(rr,'state'),'completion_state':_g(cc,'state'),'recommendation_constituency':_g(rr,'constituency'),'completion_constituency':_g(cc,'constituency'),'recommendation_category':_g(rr,'category'),'completion_category':_g(cc,'category'),'recommendation_ida':_g(rr,'ida'),'completion_ida':_g(cc,'ida'),'recommended_amount':_g(rr,'recommended_amount'),'final_amount':_g(cc,'final_amount'),'description_similarity':_num(m.match_reason,'description'),'mp_similarity':_num(m.match_reason,'mp'),'constituency_similarity':_num(m.match_reason,'constituency'),'state_similarity':_num(m.match_reason,'state'),'ida_similarity':_num(m.match_reason,'ida'),'category_similarity':_num(m.match_reason,'category'),'amount_similarity':_num(m.match_reason,'amount'),'date_score':_num(m.match_reason,'date'),'project_token_overlap':_num(m.match_reason,'token_overlap'),'match_reason':m.match_reason,'human_verdict':'','human_notes':''})
    review=pd.DataFrame(rows,columns=REVIEW_COLUMNS)
    review.to_csv(output_dir/'match_review.csv',index=False); review[review.match_tier.eq('Tier 1')].to_csv(output_dir/'tier1_review_sample.csv',index=False); review[review.match_tier.eq('Tier 2')].to_csv(output_dir/'tier2_review_sample.csv',index=False); write_html(review,output_dir/'match_review.html')
    return {'tier1_review_rows':int((review.match_tier=='Tier 1').sum()),'tier2_review_rows':int((review.match_tier=='Tier 2').sum()),'review_rows':len(review)}

def write_html(df,path):
    cards=[]
    for _,r in df.iterrows():
        metrics=''.join(f'<div class="metric"><span>{label}</span><b>{float(r[k]):.1f}</b></div>' for k,label in [('description_similarity','Description'),('mp_similarity','MP'),('constituency_similarity','Constituency'),('state_similarity','State'),('ida_similarity','IDA'),('category_similarity','Category'),('amount_similarity','Amount'),('date_score','Date')] if r.get(k,'')!='' and not pd.isna(r.get(k,'')))
        card=f'''<article class="card"><div class="top"><span class="tier">{html.escape(str(r.match_tier))}</span><b>Score {float(r.match_score):.2f}</b></div><h2>Recommendation</h2><p>{html.escape(str(r.recommendation_description))}</p><div class="meta">{html.escape(str(r.recommendation_mp))} · {html.escape(str(r.recommendation_constituency))} · {html.escape(str(r.recommendation_state))}</div><h2>Matched completion</h2><p>{html.escape(str(r.completion_description))}</p><div class="meta">{html.escape(str(r.completion_mp))} · {html.escape(str(r.completion_constituency))} · {html.escape(str(r.completion_state))}</div><div class="grid">{metrics}</div><div class="reason"><b>System evidence:</b> {html.escape(str(r.match_reason))}</div></article>'''
        cards.append(card)
    doc='''<!doctype html><html><head><meta charset="utf-8"><title>MPLADS Match Review</title><style>body{font-family:Arial,sans-serif;max-width:1050px;margin:28px auto;background:#f5f6f8;color:#20242a;padding:0 14px}.card{background:white;border:1px solid #ddd;border-radius:12px;margin:18px 0;padding:20px}.top{display:flex;justify-content:space-between;border-bottom:1px solid #eee;padding-bottom:10px}.tier{font-weight:700}.meta{color:#667085;font-size:14px;margin-bottom:14px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:15px 0}.metric{background:#f7f8fa;padding:8px;display:flex;justify-content:space-between;border-radius:7px}.reason{background:#f7f8fa;padding:12px;border-radius:8px;font-size:14px}@media(max-width:700px){.grid{grid-template-columns:repeat(2,1fr)}}</style></head><body><h1>MPLADS Match Review</h1><p>Human review aid. A match is evidence of linkage, not a fraud finding.</p>'''+''.join(cards)+'''</body></html>'''
    Path(path).write_text(doc,encoding='utf-8')
