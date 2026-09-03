# Untitled Cipher Project - SIH26102

This package contains the backend foundation for the MPLADS anomaly/risk analysis system.

## Where things go
- `backend/` = backend code and data pipeline
- `frontend/` = reserved for the Streamlit frontend
- `backend/data/raw/` = original source CSVs
- `backend/data/processed/` = intermediate files
- `backend/data/outputs/` = files consumed by Streamlit

## Run
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py --limit 1000
```

Then increase to 5000 and eventually run without `--limit` after validation.
