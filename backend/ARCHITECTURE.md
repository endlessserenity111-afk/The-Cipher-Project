# Backend architecture

```text
REAL MPLADS CSVs
      |
      v
[cleaning.py]
      |
      v
[entity_normalization.py]
      |
      v
[matching.py]
  | exact normalized entity+description
  | fuzzy retrieval fallback
  +--> Tier 1 / Tier 2 / Unmatched
      |
      v
[feature_engineering.py]
      |
      +--> cost difference
      +--> recommendation-to-completion duration
      +--> match confidence
      |
      v
[expenditure_checks.py]
      |
      +--> vendor concentration (MP-level)
      +--> payment-vs-completion mismatch (MP/IDA-level)
      |
      v
[anomaly_detection.py]
      |
      +--> IQR outliers
      +--> Isolation Forest
      |
      v
[risk_scoring.py]
      |
      +--> explainable reasons
      +--> 0-100 risk assessment
      +--> LOW / MEDIUM / HIGH
      |
      v
[aggregations.py]
      |
      v
CSV outputs --> Streamlit
```

### Key design decisions

1. `Work ID` is retained but not treated as a trusted cross-table key because the supplied tables contain very little overlap and some overlapping IDs disagree on entity/work fields.
2. Recommendations and completed works are linked through multiple signals rather than one field.
3. Tier 1 means stronger/verified linkage; Tier 2 is provisional.
4. Expenditure data has no Work ID, so expenditure anomalies stay at MP/IDA/vendor aggregate level instead of pretending to be project-level matches.
5. Isolation Forest is an anomaly detector, not a fraud classifier.
6. The risk score is an evidence score, not a probability of fraud.
