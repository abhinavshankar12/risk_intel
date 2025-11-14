"""Utility functions for ML operations."""
import os
import joblib
from typing import Optional, Any
from sqlalchemy.orm import Session
from backend.db.models import Model


def get_risk_tier(r_smoothed: float, theta_high: float = 0.7, theta_medium: float = 0.4) -> str:
    """Classify smoothed risk score into risk tier.
    
    Args:
        r_smoothed: Smoothed risk score R_{i,t}
        theta_high: Threshold for high risk
        theta_medium: Threshold for medium risk
        
    Returns:
        Risk tier: "low", "medium", or "high"
    """
    if r_smoothed >= theta_high:
        return "high"
    elif r_smoothed >= theta_medium:
        return "medium"
    else:
        return "low"


def load_active_model(db: Session) -> tuple[Any, Model]:
    """Load the currently active model from database and disk.
    
    Args:
        db: Database session
        
    Returns:
        Tuple of (loaded_model, model_metadata)
        
    Raises:
        ValueError: If no active model is found
    """
    model_record = db.query(Model).filter(Model.active_flag == True).first()  # noqa: E712
    
    if not model_record:
        raise ValueError("No active model found in database")
    
    if not model_record.model_path or not os.path.exists(model_record.model_path):
        raise ValueError(f"Model file not found: {model_record.model_path}")
    
    model = joblib.load(model_record.model_path)
    
    return model, model_record


def save_model(model: Any, model_path: str) -> None:
    """Save a trained model to disk.
    
    Args:
        model: The trained model object
        model_path: Path to save the model to
    """
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)

