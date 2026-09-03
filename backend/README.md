# SIH26102 — MPLADS Anomaly & Risk Detection Backend

Backend only. Designed for a Streamlit frontend to read the exported CSVs.

## What this pipeline does

1. Loads four MPLADS-derived CSV tables.
2. Cleans dates, money fields, text, and missing values.
3. Normalizes MP/constituency/state/IDA/category/vendor/work-description entities.
4. Matches recommended works to completed works using blocking + multi-signal fuzzy scoring.
5. Uses Tier 1 / Tier 2 / Unmatched rather than forcing weak links.
6. Engineers cost and completion-time features.
7. Adds statistical outlier flags and Isolation Forest anomaly detection.
8. Runs explainable project risk scoring.
9. Separately analyzes expenditure concentration and MP/IDA payment-completion mismatch.
10. Produces state/category/constituency rollups and validation reports.

## Important matching decision

The supplied real dataset contains a `Work ID` column in both recommended and completed files, but the observed overlap is tiny and overlapping IDs can refer to contradictory MP/work records. For that reason, this backend does NOT treat Work ID alone as a trusted cross-table key. It can be retained for reference, but matching is based on entity and content evidence.

## Important fraud-scoring decision

The system detects anomalies/risk indicators. A high score is not a finding of fraud and is not a calibrated probability of fraud.

## Folder structure

```text
.
├── config.py
├── run_pipeline.py
├── requirements.txt
├── README.md
├── src/
│   ├── cleaning.py
│   ├── entity_normalization.py
│   ├── matching.py
│   ├── feature_engineering.py
│   ├── expenditure_checks.py
│   ├── anomaly_detection.py
│   ├── risk_scoring.py
│   ├── aggregations.py
│   ├── validation.py
│   ├── io_utils.py
│   └── pipeline.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── outputs/
└── tests/
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the four supplied CSV files into `data/raw/` with the exact names expected by `config.py`, then:

```bash
python run_pipeline.py
```

Outputs go to `data/outputs/`.

## Outputs for Streamlit

- `project_risk_scores.csv`
- `high_risk_projects.csv`
- `mp_risk_indicators.csv`
- `state_rollup.csv`
- `category_rollup.csv`
- `constituency_rollup.csv`
- `match_results.csv`
- `data_quality_report.csv`
- `match_validation.csv`
- `project_validation.csv`
- `pipeline_summary.json`

## Interpretation

Project risk combines explainable rules and Isolation Forest anomaly evidence. Tier 2 matches are discounted relative to Tier 1. Expenditure evidence is intentionally aggregated at MP/IDA level because the expenditure table has no Work ID field.
