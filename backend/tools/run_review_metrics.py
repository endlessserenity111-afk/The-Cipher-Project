from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.match_metrics import write_review_metrics

if __name__ == '__main__':
    src = Path('data/outputs/review/match_review.csv')
    dst = Path('data/outputs/review/match_review_metrics.csv')
    print(write_review_metrics(src, dst).to_string(index=False))
