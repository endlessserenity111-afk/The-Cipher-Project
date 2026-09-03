import pandas as pd
from src.matching import match_records

def test_different_village_and_ida_not_verified():
    r=pd.DataFrame([{'state_norm':'andhra pradesh','constituency_norm':'rajampet','mp_norm':'midhun reddy','mp_canonical':'midhun reddy','work_norm':'providing ro water plant in ponnavolu village p kothapalli','ida_norm':'ysr kadapa district collector','ida_key':'ysrkadapa','category_norm':'normal others','category_key':'normalothers','recommended_amount':300000,'recommendation_date':pd.Timestamp('2025-02-01')}])
    c=pd.DataFrame([{'state_norm':'andhra pradesh','constituency_norm':'rajampet','mp_norm':'midhun reddy','mp_canonical':'midhun reddy','work_norm':'providing ro plant in marthuvaripalli village jogivaripalli gp','ida_norm':'chittoor district collector','ida_key':'chittoor','category_norm':'normal others','category_key':'normalothers','final_amount':283452,'completed_date':pd.Timestamp('2025-06-01')}])
    out=match_records(r,c); assert out.loc[0,'match_tier']=='Unmatched'

def test_exact_project_is_tier1():
    r=pd.DataFrame([{'state_norm':'x','constituency_norm':'y','mp_norm':'m','mp_canonical':'m','work_norm':'construction of cc road at alpha village','ida_norm':'ida1','ida_key':'ida1','category_norm':'normal others','category_key':'normalothers','recommended_amount':500000,'recommendation_date':pd.Timestamp('2025-01-01'),'work_id_key':'123'}])
    c=pd.DataFrame([{'state_norm':'x','constituency_norm':'y','mp_norm':'m','mp_canonical':'m','work_norm':'construction of cc road at alpha village','ida_norm':'ida1','ida_key':'ida1','category_norm':'normal others','category_key':'normalothers','final_amount':498000,'completed_date':pd.Timestamp('2025-03-01'),'work_id_key':'123'}])
    out=match_records(r,c); assert out.loc[0,'match_tier']=='Tier 1'
