from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "outputs"

RECOMMENDED_FILE = RAW_DIR / "mplads_recommended_works_2026-08-23.csv"
COMPLETED_FILE = RAW_DIR / "mplads_completed_works_2026-08-23.csv"
EXPENDITURE_FILE = RAW_DIR / "mplads_expenditures_2026-08-23.csv"
MP_SUMMARY_FILE = RAW_DIR / "mplads_mp_summary_2026-08-23.csv"

# Matching thresholds are intentionally conservative.
TIER1_THRESHOLD = 82.0
TIER2_THRESHOLD = 68.0
MIN_MARGIN = 6.0
MAX_CANDIDATES_PER_REC = 12
DATE_WINDOW_DAYS = 900

# Risk thresholds are in risk-score points, not probabilities of fraud.
HIGH_RISK = 70.0
MEDIUM_RISK = 45.0

RANDOM_STATE = 42
