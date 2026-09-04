# Architecture

## 1. Data layer
Four public MPLADS-derived CSVs provide recommended works, completed works, expenditures, and MP summaries.

## 2. Cleaning
Normalize columns, dates, amounts, text, and missing values. Raw files are never overwritten.

## 3. Entity normalization
Create consistent representations for MP, constituency, state, category, IDA, vendor, work description, and Work ID.

## 4. Matching
Use blocked candidate retrieval and multi-signal scoring. Work ID can corroborate a match, but it is not trusted alone. Tier 1 means high-confidence linkage; Tier 2 means provisional linkage; unmatched means no candidate met the minimum evidence threshold.

## 5. Match validation
Accepted completion records are one-to-one. Every match has score, margin, tier, and reason. A human review sample is generated for Tier 1, Tier 2, and unmatched cases.

## 6. Project features
Calculate amount deviation, duration, peer-relative cost/duration statistics, timeline-match evidence, and linkage confidence.

## 7. Expenditure evidence
Vendor concentration, payment-vs-completion mismatch, and summary-vs-transaction reconciliation are calculated at MP/constituency/IDA or MP/constituency level. These are financial indicators, not automatic fraud findings.

## 8. Anomaly detection
Use robust peer-based statistics plus Isolation Forest. Isolation Forest identifies unusual patterns; it does not know whether a record is fraudulent.

## 9. Risk scoring
Combine explainable evidence into a 0-100 analytical risk score. Tier 2 evidence is discounted. Reasons are stored for display.

## 10. Exports
CSV/JSON outputs are stable inputs for the Streamlit frontend.
