import pandas as pd
from src.matching import match_records


def _df(desc, mp='A', state='S', con='C', ida='I', cat='X', amt=100000, date='2024-01-01'):
    return pd.DataFrame([{
        'work_norm':desc,'mp_norm':mp.lower(),'mp_canonical':mp.lower(),'mp_canonical_key':mp.lower(),
        'state_norm':state.lower(),'state_norm_key':state.lower(),'constituency_norm':con.lower(),'constituency_canonical':con.lower(),
        'constituency_canonical_key':con.lower(),'ida_norm':ida.lower(),'ida_key':ida.lower(),'category_norm':cat.lower(),'category_norm_key':cat.lower(),
        'recommended_amount' if 'rec' else 'final_amount':amt,'recommendation_date' if 'rec' else 'completed_date':pd.Timestamp(date),
        'work_id_key':''
    }])


def test_strong_match_is_tier1():
    rec=pd.DataFrame([{'work_norm':'construction of cc road village a','mp_canonical':'a','mp_canonical_key':'a','mp_norm':'a','state_norm':'s','state_norm_key':'s','constituency_canonical':'c','constituency_canonical_key':'c','constituency_norm':'c','ida_norm':'i','ida_key':'i','category_norm':'x','category_norm_key':'x','recommended_amount':100000,'recommendation_date':pd.Timestamp('2024-01-01'),'work_id_key':''}])
    comp=pd.DataFrame([{'work_norm':'construction of cc road village a','mp_canonical':'a','mp_canonical_key':'a','mp_norm':'a','state_norm':'s','state_norm_key':'s','constituency_canonical':'c','constituency_canonical_key':'c','constituency_norm':'c','ida_norm':'i','ida_key':'i','category_norm':'x','category_norm_key':'x','final_amount':99000,'completed_date':pd.Timestamp('2024-04-01'),'work_id_key':''}])
    out=match_records(rec,comp)
    assert out.loc[0,'match_tier']=='Tier 1'


def test_different_description_is_not_tier1():
    rec=pd.DataFrame([{'work_norm':'ro water plant ponnavolu village','mp_canonical':'a','mp_canonical_key':'a','mp_norm':'a','state_norm':'s','state_norm_key':'s','constituency_canonical':'c','constituency_canonical_key':'c','constituency_norm':'c','ida_norm':'i1','ida_key':'i1','category_norm':'x','category_norm_key':'x','recommended_amount':300000,'recommendation_date':pd.Timestamp('2024-01-01'),'work_id_key':''}])
    comp=pd.DataFrame([{'work_norm':'ro plant marthuvaripalli village','mp_canonical':'a','mp_canonical_key':'a','mp_norm':'a','state_norm':'s','state_norm_key':'s','constituency_canonical':'c','constituency_canonical_key':'c','constituency_norm':'c','ida_norm':'i2','ida_key':'i2','category_norm':'x','category_norm_key':'x','final_amount':283000,'completed_date':pd.Timestamp('2024-03-01'),'work_id_key':''}])
    out=match_records(rec,comp)
    assert out.loc[0,'match_tier'] != 'Tier 1'
