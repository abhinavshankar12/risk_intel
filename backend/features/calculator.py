"""Feature calculation logic for risk prediction.

This module computes features for each region and date based on:
- Historical incidents (7d, 30d windows)
- Neighbor incidents
- Upcoming events
- Content signals (explicit violence calls)
- Baseline structural risk

All features are based on concrete behavior and incident data.
NO profiling based on religion, ethnicity, immigration status, or political opinion.
"""
from datetime import datetime, timedelta, date as date_type
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from backend.db.models import (
    Region, Incident, Event, ContentSignal, RegionFeature, RegionNeighbor
)


class FeatureCalculator:
    """Calculates ML features for each region and date."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def compute_features_for_region_date(
        self,
        region_id: int,
        target_date: date_type
    ) -> Dict:
        """Compute all features for a given region and date.
        
        Args:
            region_id: The region to compute features for
            target_date: The date to compute features for
            
        Returns:
            Dictionary with all computed features
        """
        region = self.db.query(Region).filter(Region.region_id == region_id).first()
        if not region:
            raise ValueError(f"Region {region_id} not found")
        
        # Convert date to datetime for queries
        target_datetime = datetime.combine(target_date, datetime.min.time())
        
        # Compute incident-based features
        incidents_7d = self._count_incidents_in_window(
            region_id, target_datetime, days=7
        )
        incidents_30d = self._count_incidents_in_window(
            region_id, target_datetime, days=30
        )
        
        # Compute neighbor incident features
        neighbor_incidents_7d = self._count_neighbor_incidents(
            region_id, target_datetime, days=7
        )
        neighbor_incidents_30d = self._count_neighbor_incidents(
            region_id, target_datetime, days=30
        )
        
        # Compute event-based features
        event_count_7d, event_attendance_7d = self._compute_event_features(
            region_id, target_datetime, days=7
        )
        
        # Get content signals
        content_violent_count = self._get_content_signal(region_id, target_date)
        
        return {
            "region_id": region_id,
            "date": target_date,
            "recent_incidents_7d": incidents_7d,
            "recent_incidents_30d": incidents_30d,
            "neighbor_incidents_7d": neighbor_incidents_7d,
            "neighbor_incidents_30d": neighbor_incidents_30d,
            "event_count_7d": event_count_7d,
            "event_attendance_7d": event_attendance_7d,
            "content_violent_count": content_violent_count,
            "baseline_risk": region.baseline_risk,
        }
    
    def _count_incidents_in_window(
        self,
        region_id: int,
        target_datetime: datetime,
        days: int
    ) -> int:
        """Count incidents in the region within the lookback window.
        
        Args:
            region_id: Region to count incidents for
            target_datetime: The target date
            days: Number of days to look back
            
        Returns:
            Count of incidents
        """
        start_datetime = target_datetime - timedelta(days=days)
        
        count = self.db.query(func.count(Incident.incident_id)).filter(
            and_(
                Incident.region_id == region_id,
                Incident.occurred_at >= start_datetime,
                Incident.occurred_at < target_datetime
            )
        ).scalar()
        
        return count or 0
    
    def _count_neighbor_incidents(
        self,
        region_id: int,
        target_datetime: datetime,
        days: int
    ) -> int:
        """Count incidents in neighboring regions within the lookback window.
        
        Args:
            region_id: Region whose neighbors to check
            target_datetime: The target date
            days: Number of days to look back
            
        Returns:
            Total count of incidents in all neighbor regions
        """
        # Get neighbor IDs
        neighbors = self.db.query(RegionNeighbor.neighbor_id).filter(
            RegionNeighbor.region_id == region_id
        ).all()
        
        if not neighbors:
            return 0
        
        neighbor_ids = [n[0] for n in neighbors]
        start_datetime = target_datetime - timedelta(days=days)
        
        count = self.db.query(func.count(Incident.incident_id)).filter(
            and_(
                Incident.region_id.in_(neighbor_ids),
                Incident.occurred_at >= start_datetime,
                Incident.occurred_at < target_datetime
            )
        ).scalar()
        
        return count or 0
    
    def _compute_event_features(
        self,
        region_id: int,
        target_datetime: datetime,
        days: int
    ) -> tuple:
        """Compute event-based features: count and total expected attendance.
        
        Args:
            region_id: Region to compute features for
            target_datetime: The target date
            days: Number of days to look forward for events
            
        Returns:
            Tuple of (event_count, total_expected_attendance)
        """
        end_datetime = target_datetime + timedelta(days=days)
        
        events = self.db.query(Event).filter(
            and_(
                Event.region_id == region_id,
                Event.start_time >= target_datetime,
                Event.start_time < end_datetime
            )
        ).all()
        
        event_count = len(events)
        total_attendance = sum(
            e.expected_attendance for e in events if e.expected_attendance
        )
        
        return event_count, total_attendance
    
    def _get_content_signal(
        self,
        region_id: int,
        target_date: date_type
    ) -> int:
        """Get content signal for a region and date.
        
        Args:
            region_id: Region ID
            target_date: Date to get signal for
            
        Returns:
            Count of posts with explicit violence calls
        """
        signal = self.db.query(ContentSignal).filter(
            and_(
                ContentSignal.region_id == region_id,
                ContentSignal.date == target_date
            )
        ).first()
        
        return signal.violent_call_post_count if signal else 0
    
    def save_features(self, features: Dict) -> RegionFeature:
        """Save computed features to the database.
        
        This operation is idempotent - it will update if exists, insert if not.
        
        Args:
            features: Dictionary of computed features
            
        Returns:
            The saved RegionFeature object
        """
        # Check if features already exist for this region and date
        existing = self.db.query(RegionFeature).filter(
            and_(
                RegionFeature.region_id == features["region_id"],
                RegionFeature.date == features["date"]
            )
        ).first()
        
        if existing:
            # Update existing record
            for key, value in features.items():
                if key not in ["region_id", "date"]:
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new record
            feature_record = RegionFeature(**features)
            self.db.add(feature_record)
            self.db.commit()
            self.db.refresh(feature_record)
            return feature_record


def compute_features_for_date(
    db: Session,
    target_date: date_type,
    region_ids: Optional[List[int]] = None
) -> List[RegionFeature]:
    """Compute and save features for all regions (or specified regions) for a given date.
    
    This is the main entry point for the feature engineering job.
    
    Args:
        db: Database session
        target_date: Date to compute features for
        region_ids: Optional list of specific region IDs. If None, compute for all regions.
        
    Returns:
        List of saved RegionFeature objects
    """
    calculator = FeatureCalculator(db)
    
    # Get regions to process
    if region_ids:
        regions = db.query(Region).filter(Region.region_id.in_(region_ids)).all()
    else:
        regions = db.query(Region).all()
    
    results = []
    for region in regions:
        try:
            features = calculator.compute_features_for_region_date(
                region.region_id,
                target_date
            )
            saved_feature = calculator.save_features(features)
            results.append(saved_feature)
        except Exception as e:
            print(f"Error computing features for region {region.region_id}: {e}")
            continue
    
    return results

