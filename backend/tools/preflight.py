from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import RECOMMENDED_FILE, COMPLETED_FILE, EXPENDITURE_FILE, MP_SUMMARY_FILE

required=[RECOMMENDED_FILE,COMPLETED_FILE,EXPENDITURE_FILE,MP_SUMMARY_FILE]
missing=[p for p in required if not p.exists()]
if missing:
    print('MISSING INPUTS:')
    for p in missing: print(' -',p)
    raise SystemExit(1)
print('Preflight OK. All four MPLADS input files are present.')
