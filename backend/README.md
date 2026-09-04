# MPLADS Backend (SIH26102)

This directory contains the analytical backend for the SIH26102 MPLADS transparency and anomaly-detection project.

## Important wording
The system identifies **anomalies and risk indicators**. It does not prove fraud, misconduct, or guilt, and risk scores are not probabilities of fraud.

## Architecture & Documentation
Please see the `docs/` folder for detailed documentation on architecture, outputs, data safety, and the frontend contract.

## Pipeline
raw data -> cleaning -> entity normalization -> multi-signal matching -> match validation -> feature engineering -> expenditure analysis -> statistical anomalies -> Isolation Forest -> explainable risk score -> aggregation -> review/export

## Quickstart

1. **Place raw data:**
   Put the four real MPLADS CSVs in `data/raw/`:
   - `mplads_recommended_works_2026-08-23.csv`
   - `mplads_completed_works_2026-08-23.csv`
   - `mplads_expenditures_2026-08-23.csv`
   - `mplads_mp_summary_2026-08-23.csv`

2. **Setup environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run pipeline (fast demo):**
   ```bash
   python run_pipeline.py --limit 100
   ```

4. **Review matches:**
   ```bash
   python tools/review_matches.py --all
   ```
   *The browser-friendly review page will be generated at `data/outputs/review/match_review.html`.*

## Review Modes
```bash
python tools/review_matches.py --tier1
python tools/review_matches.py --tier2
python tools/review_matches.py --unmatched
```

## Data Integrity Principles
- Raw inputs are never overwritten.
- Work ID is corroborating evidence, not an unconditional truth source.
- Accepted project links are one-to-one with completion rows.
- Weak matches are left unmatched rather than forced.
- Project-level and MP/IDA-level expenditure evidence are kept separate.
