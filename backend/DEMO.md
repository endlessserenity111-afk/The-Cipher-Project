# Fast demo

After a reboot:

```bash
cd ~/Documents/Cipher/Untitled-Cipher-Project-Backend/backend
source .venv/bin/activate
python run_pipeline.py --limit 100
python tools/review_matches.py --all
```

To only review one bucket:

```bash
python tools/review_matches.py --tier1
python tools/review_matches.py --tier2
python tools/review_matches.py --unmatched
```

The browser-friendly review page is `data/outputs/review/match_review.html`.
