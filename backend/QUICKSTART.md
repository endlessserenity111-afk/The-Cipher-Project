# Quick start

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Put the four real CSVs into `data/raw/` with the names used in `config.py`.

### Fast smoke test

```bash
python run_pipeline.py --limit 1000
```

### Larger validation run

```bash
python run_pipeline.py --limit 5000
```

### Full run

```bash
python run_pipeline.py
```

All outputs land in `data/outputs/`.

### Unit tests

```bash
python -m pytest -q
```
