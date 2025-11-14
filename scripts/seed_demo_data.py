"""Seed database with demo data for testing and development.

This script creates:
- 20 demo regions with baseline risk scores
- Regional adjacency relationships
- Historical incidents over the past 90 days
- Upcoming events
- Content signals
- Sample features and risk scores
"""
import os
import sys
from datetime import datetime, timedelta, date as date_type
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from backend.db.base import SessionLocal, engine, Base
from backend.db.models import (
    Region, RegionNeighbor, Incident, Event, ContentSignal,
    RegionFeature, RiskScore, Model, AuditLog
)
from backend.features.calculator import compute_features_for_date
from backend.ml.training import train_model
from backend.ml.scoring import score_regions_for_date


# Demo region names
DEMO_REGIONS = [
    "Downtown Metro", "West Side District", "East Harbor", "North Quarter",
    "South End", "Midtown", "Financial District", "Old Town", "University Area",
    "Industrial Park", "Riverside", "Hillside", "Lakefront", "Airport Zone",
    "Suburban North", "Suburban South", "Suburban East", "Suburban West",
    "Rural County A", "Rural County B"
]

INCIDENT_TYPES = ["assault", "threat", "vandalism", "weapons_offense", "suspicious_activity"]
EVENT_TYPES = ["large_gathering", "infrastructure_event", "public_ceremony", "sporting_event"]


def create_regions(db):
    """Create demo regions."""
    print("Creating regions...")
    regions = []
    
    for i, name in enumerate(DEMO_REGIONS):
        # Assign baseline risk based on "urban" vs "rural" - structural factors only
        if "Rural" in name:
            baseline_risk = random.uniform(0.1, 0.3)
        elif "Suburban" in name:
            baseline_risk = random.uniform(0.2, 0.4)
        else:
            baseline_risk = random.uniform(0.3, 0.6)
        
        region = Region(
            name=name,
            baseline_risk=baseline_risk,
            geom=None  # Can add actual geometry later
        )
        db.add(region)
        regions.append(region)
    
    db.commit()
    print(f"Created {len(regions)} regions")
    return regions


def create_neighbor_relationships(db, regions):
    """Create adjacency relationships between regions."""
    print("Creating neighbor relationships...")
    
    count = 0
    for i, region in enumerate(regions):
        # Each region is neighbors with 2-4 nearby regions
        num_neighbors = random.randint(2, 4)
        neighbor_indices = random.sample(
            [j for j in range(len(regions)) if j != i],
            min(num_neighbors, len(regions) - 1)
        )
        
        for neighbor_idx in neighbor_indices:
            neighbor = RegionNeighbor(
                region_id=region.region_id,
                neighbor_id=regions[neighbor_idx].region_id,
                weight=1.0
            )
            db.add(neighbor)
            count += 1
    
    db.commit()
    print(f"Created {count} neighbor relationships")


def create_historical_incidents(db, regions, days=90):
    """Create historical incidents for the past N days."""
    print(f"Creating historical incidents for past {days} days...")
    
    incidents = []
    end_date = datetime.utcnow()
    
    for region in regions:
        # Number of incidents varies by baseline risk
        # Higher baseline = more incidents (structural factors)
        avg_incidents_per_month = int(region.baseline_risk * 20)
        
        for _ in range(int(avg_incidents_per_month * (days / 30))):
            occurred_at = end_date - timedelta(
                days=random.uniform(0, days),
                hours=random.uniform(0, 24)
            )
            
            incident = Incident(
                region_id=region.region_id,
                occurred_at=occurred_at,
                type=random.choice(INCIDENT_TYPES),
                severity=random.uniform(0.3, 0.9),
                source="law_enforcement"
            )
            db.add(incident)
            incidents.append(incident)
    
    db.commit()
    print(f"Created {len(incidents)} historical incidents")


def create_upcoming_events(db, regions, days=14):
    """Create upcoming events for the next N days."""
    print(f"Creating upcoming events for next {days} days...")
    
    events = []
    start_date = datetime.utcnow()
    
    for region in regions:
        # 30% chance of having an event
        if random.random() < 0.3:
            num_events = random.randint(1, 3)
            
            for _ in range(num_events):
                start_time = start_date + timedelta(
                    days=random.uniform(0, days),
                    hours=random.uniform(0, 24)
                )
                
                event = Event(
                    region_id=region.region_id,
                    start_time=start_time,
                    end_time=start_time + timedelta(hours=random.uniform(2, 8)),
                    type=random.choice(EVENT_TYPES),
                    expected_attendance=random.randint(100, 10000)
                )
                db.add(event)
                events.append(event)
    
    db.commit()
    print(f"Created {len(events)} upcoming events")


def create_content_signals(db, regions, days=30):
    """Create content signals for the past N days."""
    print(f"Creating content signals for past {days} days...")
    
    signals = []
    end_date = date_type.today()
    
    for region in regions:
        for day_offset in range(days):
            signal_date = end_date - timedelta(days=day_offset)
            
            # Simulate content signals with some randomness
            # Occasional spikes in explicit violence calls
            if random.random() < 0.1:  # 10% chance of elevated signal
                violent_count = random.randint(5, 20)
            else:
                violent_count = random.randint(0, 3)
            
            signal = ContentSignal(
                region_id=region.region_id,
                date=signal_date,
                violent_call_post_count=violent_count
            )
            db.add(signal)
            signals.append(signal)
    
    db.commit()
    print(f"Created {len(signals)} content signals")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("RISK INTELLIGENCE PLATFORM - DEMO DATA SEEDER")
    print("=" * 60)
    print()
    
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created")
    print()
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_regions = db.query(Region).count()
        if existing_regions > 0:
            print(f"Warning: Database already contains {existing_regions} regions")
            response = input("Do you want to continue and add more data? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborting")
                return
        
        # Seed data
        regions = create_regions(db)
        create_neighbor_relationships(db, regions)
        create_historical_incidents(db, regions, days=90)
        create_upcoming_events(db, regions, days=14)
        create_content_signals(db, regions, days=30)
        
        print()
        print("=" * 60)
        print("COMPUTING FEATURES")
        print("=" * 60)
        print()
        
        # Compute features for the past 30 days
        print("Computing features for past 30 days...")
        today = date_type.today()
        for day_offset in range(30):
            target_date = today - timedelta(days=day_offset)
            features = compute_features_for_date(db, target_date)
            if day_offset == 0:
                print(f"  {target_date}: computed {len(features)} feature records")
            elif day_offset % 5 == 0:
                print(f"  {target_date}: computed {len(features)} feature records")
        
        print()
        print("=" * 60)
        print("TRAINING MODEL")
        print("=" * 60)
        print()
        
        # Train a logistic regression model
        print("Training logistic regression model...")
        model_record = train_model(
            db=db,
            algorithm="logistic_regression",
            start_date=today - timedelta(days=60),
            end_date=today - timedelta(days=8),  # Leave recent days for scoring
            set_active=True,
            actor="demo_seeder"
        )
        
        print()
        print("=" * 60)
        print("COMPUTING RISK SCORES")
        print("=" * 60)
        print()
        
        # Score the past 7 days
        print("Computing risk scores for past 7 days...")
        for day_offset in range(7):
            target_date = today - timedelta(days=day_offset)
            scores = score_regions_for_date(db, target_date, actor="demo_seeder")
            print(f"  {target_date}: scored {len(scores)} regions")
        
        print()
        print("=" * 60)
        print("DEMO DATA SEEDING COMPLETE!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  - Regions: {len(regions)}")
        print(f"  - Incidents: {db.query(Incident).count()}")
        print(f"  - Events: {db.query(Event).count()}")
        print(f"  - Content Signals: {db.query(ContentSignal).count()}")
        print(f"  - Features: {db.query(RegionFeature).count()}")
        print(f"  - Risk Scores: {db.query(RiskScore).count()}")
        print(f"  - Models: {db.query(Model).count()}")
        print(f"  - Audit Logs: {db.query(AuditLog).count()}")
        print()
        print("You can now start the backend server and frontend to explore the data!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

