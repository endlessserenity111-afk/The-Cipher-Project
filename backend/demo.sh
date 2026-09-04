#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
python run_pipeline.py --limit 100
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open data/outputs/review/match_review.html >/dev/null 2>&1 || true
fi
