# Quick Start

```bash
cd backend
source .venv/bin/activate
pytest -q
python run_pipeline.py --limit 100
python tools/review_matches.py --all
python tools/run_review_metrics.py
```

Open `data/outputs/review/match_review.html` in Chrome for a visual review page.

For a full run, use `python run_pipeline.py` only after the 100/1000/5000 row runs look sensible.
