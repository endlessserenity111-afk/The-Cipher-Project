# Data safety and interpretation rules

1. Files under `data/raw/` are source inputs. The pipeline never writes back into them.
2. Raw CSV files are ignored by Git to avoid accidental large-file commits.
3. A matching tier is a linkage confidence label, not a fraud label.
4. Risk scores are analytical assessments, not probabilities of fraud.
5. Vendor concentration, payment/completion mismatch, and reconciliation differences are risk/review indicators. They are not proof of wrongdoing.
6. The expenditure table does not contain a reliable Work ID, so project-level expenditure attribution is deliberately not claimed.
7. Human review should be used to assess sampled matches and improve thresholds.
