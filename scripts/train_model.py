"""Command-line script to train a new model."""
import os
import sys
import argparse
from datetime import datetime, timedelta, date as date_type

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from backend.db.base import SessionLocal
from backend.ml.training import train_model


def main():
    parser = argparse.ArgumentParser(description='Train a risk prediction model')
    parser.add_argument(
        '--algorithm',
        choices=['logistic_regression', 'xgboost', 'lightgbm'],
        default='xgboost',
        help='ML algorithm to use (default: xgboost)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days of training data (default: 90)'
    )
    parser.add_argument(
        '--holdout',
        type=int,
        default=7,
        help='Number of recent days to hold out for validation (default: 7)'
    )
    parser.add_argument(
        '--version',
        type=str,
        help='Model version string (auto-generated if not provided)'
    )
    parser.add_argument(
        '--activate',
        action='store_true',
        help='Set this model as active immediately'
    )
    parser.add_argument(
        '--actor',
        type=str,
        default='manual_training',
        help='Actor name for audit log (default: manual_training)'
    )
    
    args = parser.parse_args()
    
    # Calculate date range
    end_date = date_type.today() - timedelta(days=args.holdout)
    start_date = end_date - timedelta(days=args.days)
    
    print("=" * 60)
    print("MODEL TRAINING")
    print("=" * 60)
    print(f"Algorithm: {args.algorithm}")
    print(f"Training period: {start_date} to {end_date}")
    print(f"Will activate: {'Yes' if args.activate else 'No'}")
    print()
    
    # Confirm
    response = input("Proceed with training? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted")
        return
    
    # Train
    db = SessionLocal()
    try:
        model = train_model(
            db=db,
            algorithm=args.algorithm,
            start_date=start_date,
            end_date=end_date,
            model_version=args.version,
            set_active=args.activate,
            actor=args.actor
        )
        
        print()
        print("=" * 60)
        print("TRAINING COMPLETE")
        print("=" * 60)
        print(f"Model Version: {model.model_version}")
        print(f"Active: {model.active_flag}")
        print(f"Metrics:")
        for key, value in model.metrics_json.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error during training: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

