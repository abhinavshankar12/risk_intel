"""Command-line script to score regions for a specific date."""
import os
import sys
import argparse
from datetime import datetime, date as date_type

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from backend.db.base import SessionLocal
from backend.ml.scoring import score_regions_for_date


def main():
    parser = argparse.ArgumentParser(description='Score regions for a specific date')
    parser.add_argument(
        '--date',
        type=str,
        help='Date to score (YYYY-MM-DD format). Defaults to today.'
    )
    parser.add_argument(
        '--actor',
        type=str,
        default='manual_scoring',
        help='Actor name for audit log (default: manual_scoring)'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        help='Override ALPHA parameter'
    )
    parser.add_argument(
        '--beta',
        type=float,
        help='Override BETA parameter'
    )
    parser.add_argument(
        '--gamma',
        type=float,
        help='Override GAMMA parameter'
    )
    parser.add_argument(
        '--delta',
        type=float,
        help='Override DELTA parameter'
    )
    
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print("Error: Date must be in YYYY-MM-DD format")
            sys.exit(1)
    else:
        target_date = date_type.today()
    
    print("=" * 60)
    print("RISK SCORING")
    print("=" * 60)
    print(f"Date: {target_date}")
    if args.alpha: print(f"ALPHA: {args.alpha}")
    if args.beta: print(f"BETA: {args.beta}")
    if args.gamma: print(f"GAMMA: {args.gamma}")
    if args.delta: print(f"DELTA: {args.delta}")
    print()
    
    # Score
    db = SessionLocal()
    try:
        scores = score_regions_for_date(
            db=db,
            target_date=target_date,
            alpha=args.alpha,
            beta=args.beta,
            gamma=args.gamma,
            delta=args.delta,
            actor=args.actor
        )
        
        print()
        print("=" * 60)
        print("SCORING COMPLETE")
        print("=" * 60)
        print(f"Regions scored: {len(scores)}")
        
        # Show distribution
        tiers = {'high': 0, 'medium': 0, 'low': 0}
        for score in scores:
            tiers[score.risk_tier] += 1
        
        print(f"Distribution:")
        print(f"  High: {tiers['high']}")
        print(f"  Medium: {tiers['medium']}")
        print(f"  Low: {tiers['low']}")
        
    except Exception as e:
        print(f"Error during scoring: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

