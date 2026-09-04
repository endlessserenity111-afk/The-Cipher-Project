from pathlib import Path
import pandas as pd
from src.match_review import build_review_samples


def test_review_samples_created(tmp_path):
    matches=pd.DataFrame([
        {'recommendation_index':0,'completion_index':0,'match_score':95,'match_tier':'Tier 1','match_confidence':'Verified','score_margin':10,'best_candidate_index':0,'best_candidate_score':95,'match_reason':'fuzzy; description=98; mp=100; constituency=100; state=100; ida=100; category=100; amount=99; timeline=80; token_overlap=80'},
        {'recommendation_index':1,'completion_index':1,'match_score':80,'match_tier':'Tier 2','match_confidence':'Provisional','score_margin':5,'best_candidate_index':1,'best_candidate_score':80,'match_reason':'fuzzy; description=85; mp=100; constituency=100; state=100; ida=100; category=100; amount=90; timeline=70; token_overlap=60'},
        {'recommendation_index':2,'completion_index':-1,'match_score':0,'match_tier':'Unmatched','match_confidence':'Unmatched','score_margin':0,'best_candidate_index':1,'best_candidate_score':68,'match_reason':'best candidate did not reach a match tier'},
    ])
    rec=pd.DataFrame([{'work_id':'r1','work_description':'road a','mp_name':'A','state':'S','constituency':'C','category':'X','ida':'I','recommended_amount':100},{'work_id':'r2','work_description':'road b','mp_name':'A','state':'S','constituency':'C','category':'X','ida':'I','recommended_amount':100},{'work_id':'r3','work_description':'road c','mp_name':'A','state':'S','constituency':'C','category':'X','ida':'I','recommended_amount':100}])
    comp=pd.DataFrame([{'work_id':'c1','work_description':'road a','mp_name':'A','state':'S','constituency':'C','category':'X','ida':'I','final_amount':99},{'work_id':'c2','work_description':'road b','mp_name':'A','state':'S','constituency':'C','category':'X','ida':'I','final_amount':98}])
    info=build_review_samples(matches,rec,comp,tmp_path)
    assert info['review_rows']==3
    assert (tmp_path/'match_review.html').exists()
