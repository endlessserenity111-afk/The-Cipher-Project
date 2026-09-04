from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
summary_path = ROOT / 'data' / 'outputs' / 'pipeline_summary.json'
checks = ROOT / 'data' / 'outputs'
required = [
    'data_quality_report.csv','match_results.csv','match_validation.csv',
    'project_risk_scores.csv','high_risk_projects.csv','mp_risk_indicators.csv',
    'state_rollup.csv','category_rollup.csv','constituency_rollup.csv',
    'project_validation.csv','output_validation.csv',
]
missing=[x for x in required if not (checks/x).exists()]
if missing:
    print('Missing outputs:')
    for x in missing: print(' -',x)
    raise SystemExit(1)
if not summary_path.exists():
    raise SystemExit('pipeline_summary.json not found')
summary=json.loads(summary_path.read_text(encoding='utf-8'))
print('Output check OK.')
print(f"Mode: {summary.get('mode')}, recommendations: {summary.get('recommendations')}, Tier 1: {summary.get('tier1_matches')}, Tier 2: {summary.get('tier2_matches')}, unmatched: {summary.get('unmatched')}")
