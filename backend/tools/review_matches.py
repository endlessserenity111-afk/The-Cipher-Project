#!/usr/bin/env python3
from pathlib import Path
import argparse,pandas as pd

def money(x):
    try:return f'₹{float(x):,.0f}'
    except:return str(x) if str(x)!='nan' else '—'

def show(r,n,total):
    print('\n'+'='*84); print(f'MATCH REVIEW {n}/{total} | {r.match_tier} | score={float(r.match_score):.2f}'); print('='*84)
    print('\nRECOMMENDATION'); print('  '+str(r.recommendation_description)); print(f'  MP: {r.recommendation_mp} | Constituency: {r.recommendation_constituency} | State: {r.recommendation_state}'); print(f'  Category: {r.recommendation_category} | Amount: {money(r.recommended_amount)}')
    print('\nMATCHED COMPLETION'); print('  '+str(r.completion_description)); print(f'  MP: {r.completion_mp} | Constituency: {r.completion_constituency} | State: {r.completion_state}'); print(f'  Category: {r.completion_category} | Final amount: {money(r.final_amount)}')
    print('\nEVIDENCE')
    for k,label in [('description_similarity','Description'),('mp_similarity','MP'),('constituency_similarity','Constituency'),('state_similarity','State'),('ida_similarity','IDA'),('category_similarity','Category'),('amount_similarity','Amount'),('date_score','Date')]:
        v=r.get(k,'')
        if v=='' or pd.isna(v):continue
        v=float(v); mark='✓' if v>=90 else '~' if v>=75 else '!'; print(f'  {mark} {label:<16} {v:5.1f}')
    print('\nSYSTEM EVIDENCE'); print('  '+str(r.match_reason))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--file',default='data/outputs/review/match_review.csv'); a=ap.parse_args(); p=Path(a.file)
    if not p.exists():raise SystemExit(f'Review file not found: {p}. Run pipeline first.')
    d=pd.read_csv(p); d['human_verdict']=d.get('human_verdict','').fillna(''); d['human_notes']=d.get('human_notes','').fillna(''); pending=[i for i in d.index if str(d.at[i,'human_verdict']).upper() not in {'ACCEPT','REJECT'}]
    print(f'Pending reviews: {len(pending)} / {len(d)}'); print('Commands: y=accept, n=reject, s=skip, q=quit')
    for pos,i in enumerate(pending,1):
        show(d.loc[i],pos,len(pending)); c=input('\nYour verdict [y/n/s/q]: ').strip().lower()
        if c=='q':break
        if c=='s':continue
        if c not in {'y','n'}:print('Invalid choice; skipped.');continue
        d.at[i,'human_verdict']='ACCEPT' if c=='y' else 'REJECT'; d.at[i,'human_notes']=input('Optional note: ').strip(); d.to_csv(p,index=False)
    print('\nSaved decisions to',p)
if __name__=='__main__':main()
