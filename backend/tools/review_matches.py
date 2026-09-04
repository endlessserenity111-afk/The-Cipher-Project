import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd


def _show(row, number, total):
    print("\n" + "=" * 90)
    print(f"MATCH REVIEW {number}/{total} | {row['review_type'].upper()} | {row['match_tier']} | score={float(row['match_score'] or 0):.2f}")
    print("=" * 90)
    print("\nRECOMMENDATION")
    print(f"  Work         : {row['recommendation_description']}")
    print(f"  MP           : {row['recommendation_mp']}")
    print(f"  Constituency : {row['recommendation_constituency']}")
    print(f"  State        : {row['recommendation_state']}")
    print(f"  Category     : {row['recommendation_category']}")
    print(f"  Amount       : {row['recommended_amount']}")
    if row['review_type'] == 'unmatched':
        print("\nBEST REJECTED CANDIDATE")
        print(f"  Work         : {row['best_candidate_description']}")
        print(f"  MP           : {row['best_candidate_mp']}")
        print(f"  Score        : {row['best_candidate_score']}")
    else:
        print("\nMATCHED COMPLETION")
        print(f"  Work         : {row['completion_description']}")
        print(f"  MP           : {row['completion_mp']}")
        print(f"  Constituency : {row['completion_constituency']}")
        print(f"  State        : {row['completion_state']}")
        print(f"  Category     : {row['completion_category']}")
        print(f"  Final amount : {row['final_amount']}")
        print("\nEVIDENCE")
        for key,label in [
            ('description_similarity','Description'),('mp_similarity','MP'),('constituency_similarity','Constituency'),
            ('state_similarity','State'),('ida_similarity','IDA'),('category_similarity','Category'),
            ('amount_similarity','Amount'),('timeline_match_score','Timeline')]:
            value=row.get(key,'')
            if value != '' and not pd.isna(value): print(f"  {label:<15}: {float(value):6.1f}")
    print("\nSYSTEM EVIDENCE")
    print(f"  {row['match_reason']}")


def main():
    parser=argparse.ArgumentParser(description="Review selected MPLADS match samples.")
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--tier1',action='store_true',help='Review Tier 1 only')
    group.add_argument('--tier2',action='store_true',help='Review Tier 2 only')
    group.add_argument('--unmatched',action='store_true',help='Review unmatched samples only')
    parser.add_argument('--all',action='store_true',help='Review all generated samples')
    parser.add_argument('--file',default='data/outputs/review/match_review.csv')
    args=parser.parse_args()
    path=Path(args.file)
    if not path.exists():
        raise FileNotFoundError(f"Review file not found: {path}. Run the pipeline first.")
    df=pd.read_csv(path).fillna('')
    if args.tier1: df=df[df.match_tier=='Tier 1']
    elif args.tier2: df=df[df.match_tier=='Tier 2']
    elif args.unmatched: df=df[df.review_type=='unmatched']
    elif not args.all: pass
    if df.empty:
        print('No review records found for this selection.')
        return
    df=df.reset_index(drop=True)
    for i,(_,row) in enumerate(df.iterrows(),1):
        _show(row,i,len(df))
        while True:
            try: choice=input("\nHuman review [y=accept / n=reject / s=skip / q=quit]: ").strip().lower()
            except EOFError: choice='q'
            if choice in {'y','n','s','q'}: break
            print('Please enter y, n, s, or q.')
        if choice=='q': break
        verdict={'y':'ACCEPT','n':'REJECT','s':'SKIP'}[choice]
        df.loc[i-1,'human_verdict']=verdict
        note=input('Optional note (press Enter to skip): ').strip() if choice!='s' else ''
        df.loc[i-1,'human_notes']=note
        df.to_csv(path,index=False)
    print('\nReview saved to:', path)


if __name__=='__main__':
    main()
