"""Command-line script to compute features for a date."""
import os
import sys
import argparse
from datetime import datetime, date as date_type

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from backend.db.base import SessionLocal
from backend.features.calculator import compute_features_for_date


def main():
    parser = argparse.ArgumentParser(description='Compute features for a specific date')
    parser.add_argument(
        '--date',
        type=str,
        help='Date to compute features for (YYYY-MM-DD format). Defaults to today.'
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
    print("FEATURE COMPUTATION")
    print("=" * 60)
    print(f"Date: {target_date}")
    print()
    
    # Compute
    db = SessionLocal()
    try:
        features = compute_features_for_date(db, target_date)
        
        print()
        print("=" * 60)
        print("COMPUTATION COMPLETE")
        print("=" * 60)
        print(f"Features computed: {len(features)} region(s)")
        
        if features:
            # Show sample
            sample = features[0]
            print(f"\nSample (Region {sample.region_id}):")
            print(f"  Recent incidents (7d): {sample.recent_incidents_7d}")
            print(f"  Recent incidents (30d): {sample.recent_incidents_30d}")
            print(f"  Neighbor incidents (7d): {sample.neighbor_incidents_7d}")
            print(f"  Event count (7d): {sample.event_count_7d}")
            print(f"  Content violent count: {sample.content_violent_count}")
            print(f"  Baseline risk: {sample.baseline_risk:.3f}")
        
    except Exception as e:
        print(f"Error during feature computation: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

