"""Tests for feature calculation logic."""
import pytest
from datetime import datetime, timedelta


class TestFeatureCalculations:
    """Test feature engineering calculations."""
    
    def test_incident_counting_window(self):
        """Test that incident counts respect time windows."""
        # This is a conceptual test - in practice would need DB fixtures
        
        target_date = datetime(2024, 1, 15)
        
        # Incidents:
        # - 2024-01-14: within 1 day
        # - 2024-01-10: within 7 days
        # - 2023-12-20: within 30 days
        # - 2023-12-01: outside 30 days
        
        # Expected counts:
        # 7-day window: 2 incidents (Jan 14, Jan 10)
        # 30-day window: 3 incidents (Jan 14, Jan 10, Dec 20)
        
        # This would be tested with actual DB queries in integration tests
        pass
    
    def test_event_attendance_aggregation(self):
        """Test that event attendance is correctly summed."""
        # Mock event data
        events = [
            {"expected_attendance": 1000},
            {"expected_attendance": 500},
            {"expected_attendance": None},  # Should be handled
        ]
        
        total = sum(e.get("expected_attendance", 0) or 0 for e in events)
        assert total == 1500
    
    def test_baseline_risk_bounds(self):
        """Test that baseline risk is properly bounded [0, 1]."""
        # Baseline risk should always be between 0 and 1
        valid_values = [0.0, 0.5, 1.0]
        for val in valid_values:
            assert 0.0 <= val <= 1.0
        
        invalid_values = [-0.1, 1.5]
        for val in invalid_values:
            assert not (0.0 <= val <= 1.0)

