import pandas as pd
from src.match_review import build_review_samples

def test_review_outputs(tmp_path):
    m=pd.DataFrame([{'recommendation_index':0,'completion_index':0,'match_score':95,'match_tier':'Tier 1','match_confidence':'Verified','score_margin':12,'match_reason':'description=95; mp=100; constituency=100; state=100; ida=100; category=100; amount=99; date=90; token_overlap=80'}])
    r=pd.DataFrame([{'work_id':1,'work_description':'x','mp_name':'m','state':'s','constituency':'c','category':'cat','ida':'i','recommended_amount':1}]); c=pd.DataFrame([{'work_id':2,'work_description':'x','mp_name':'m','state':'s','constituency':'c','category':'cat','ida':'i','final_amount':1}])
    s=build_review_samples(m,r,c,tmp_path); assert s['review_rows']==1; assert (tmp_path/'match_review.html').exists()
