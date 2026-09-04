# MPLADS SIH26102 Backend

This repository contains the analytical backend for the SIH26102 MPLADS transparency and anomaly-detection project.

## Important wording
The system identifies **anomalies and risk indicators**. It does not prove fraud, misconduct, or guilt, and risk scores are not probabilities of fraud.

## Pipeline
raw data -> cleaning -> entity normalization -> multi-signal matching -> match validation -> feature engineering -> expenditure analysis -> statistical anomalies -> Isolation Forest -> explainable risk score -> aggregation -> review/export

## Inputs
Place the four real MPLADS CSVs in `data/raw/`:

- `mplads_recommended_works_2026-08-23.csv`
- `mplads_completed_works_2026-08-23.csv`
- `mplads_expenditures_2026-08-23.csv`
- `mplads_mp_summary_2026-08-23.csv`

Raw CSVs are intentionally ignored by Git.

## Run
```bash
source .venv/bin/activate
pytest -q
python run_pipeline.py --limit 100
python tools/review_matches.py --all
python tools/run_review_metrics.py
```

For larger runs:
```bash
python run_pipeline.py --limit 1000
python run_pipeline.py --limit 5000
python run_pipeline.py
```

## Review modes
```bash
python tools/review_matches.py --tier1
python tools/review_matches.py --tier2
python tools/review_matches.py --unmatched
python tools/review_matches.py --all
```

Generated review files live under `data/outputs/review/`.

## Data integrity principles
- Raw inputs are never overwritten.
- Work ID is corroborating evidence, not an unconditional truth source.
- Accepted project links are one-to-one with completion rows.
- Weak matches are left unmatched rather than forced.
- Project-level and MP/IDA-level expenditure evidence are kept separate.

## Recommended validation ladder
Use 100, then 1,000, then 5,000 recommendations before the full run. Review the three match buckets at each stage. The code intentionally favors precision and auditability over forcing more matches.
