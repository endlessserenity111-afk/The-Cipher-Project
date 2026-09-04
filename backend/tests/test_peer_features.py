import pandas as pd
from src.feature_engineering import add_peer_features


def test_peer_features_are_created():
    rows=[]
    for i in range(15):
        rows.append({'recommendation_row_id':i,'state':'S','category':'Roads','amount_difference_pct':10+i,'days_to_completion':100+i})
    out=add_peer_features(pd.DataFrame(rows), min_group=10)
    assert 'cost_percentile' in out.columns
    assert 'duration_percentile' in out.columns
    assert out['cost_percentile'].between(0,100).all()
