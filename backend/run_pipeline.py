import argparse
import json
from src.pipeline import run_pipeline


def main():
    parser=argparse.ArgumentParser(description="Run the SIH26102 MPLADS analytics backend.")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N recommendations. Completion/expenditure tables remain available as context.")
    args=parser.parse_args()
    summary=run_pipeline(args.limit)
    print("\nMPLADS backend pipeline completed.\n")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
