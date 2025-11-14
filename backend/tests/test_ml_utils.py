"""Tests for ML utility functions."""
import pytest
from backend.ml.utils import get_risk_tier


class TestRiskTier:
    """Test risk tier classification logic."""
    
    def test_high_risk_tier(self):
        """Test that scores >= theta_high are classified as high."""
        assert get_risk_tier(0.7, theta_high=0.7, theta_medium=0.4) == "high"
        assert get_risk_tier(0.8, theta_high=0.7, theta_medium=0.4) == "high"
        assert get_risk_tier(1.0, theta_high=0.7, theta_medium=0.4) == "high"
    
    def test_medium_risk_tier(self):
        """Test that scores in [theta_medium, theta_high) are classified as medium."""
        assert get_risk_tier(0.4, theta_high=0.7, theta_medium=0.4) == "medium"
        assert get_risk_tier(0.5, theta_high=0.7, theta_medium=0.4) == "medium"
        assert get_risk_tier(0.69, theta_high=0.7, theta_medium=0.4) == "medium"
    
    def test_low_risk_tier(self):
        """Test that scores < theta_medium are classified as low."""
        assert get_risk_tier(0.0, theta_high=0.7, theta_medium=0.4) == "low"
        assert get_risk_tier(0.2, theta_high=0.7, theta_medium=0.4) == "low"
        assert get_risk_tier(0.39, theta_high=0.7, theta_medium=0.4) == "low"
    
    def test_boundary_values(self):
        """Test exact boundary values."""
        # Exactly at theta_high
        assert get_risk_tier(0.7, theta_high=0.7, theta_medium=0.4) == "high"
        
        # Exactly at theta_medium
        assert get_risk_tier(0.4, theta_high=0.7, theta_medium=0.4) == "medium"
        
        # Just below theta_medium
        assert get_risk_tier(0.3999, theta_high=0.7, theta_medium=0.4) == "low"
    
    def test_custom_thresholds(self):
        """Test with different threshold values."""
        assert get_risk_tier(0.9, theta_high=0.9, theta_medium=0.5) == "high"
        assert get_risk_tier(0.7, theta_high=0.9, theta_medium=0.5) == "medium"
        assert get_risk_tier(0.3, theta_high=0.9, theta_medium=0.5) == "low"

