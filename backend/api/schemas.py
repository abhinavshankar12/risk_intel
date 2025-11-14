"""Pydantic schemas for API requests and responses."""
from datetime import datetime, date as date_type
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RegionResponse(BaseModel):
    """Response schema for region data."""
    region_id: int
    name: str
    baseline_risk: float
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RiskScoreResponse(BaseModel):
    """Response schema for risk scores."""
    id: int
    region_id: int
    date: date_type
    p_raw: float = Field(..., description="Raw model prediction probability")
    r_smoothed: float = Field(..., description="Smoothed risk score")
    risk_tier: str = Field(..., description="Risk tier: low, medium, or high")
    model_version: str
    neighbor_avg_p: Optional[float] = None
    prev_r: Optional[float] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    """Response schema for incidents."""
    incident_id: int
    region_id: int
    occurred_at: datetime
    type: str
    severity: float
    source: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ModelResponse(BaseModel):
    """Response schema for models."""
    id: int
    model_version: str
    trained_at: datetime
    algorithm: str
    metrics_json: Dict[str, Any]
    active_flag: bool
    config_json: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Response schema for audit logs."""
    id: int
    created_at: datetime
    actor: str
    action_type: str
    payload_json: Dict[str, Any]
    
    class Config:
        from_attributes = True


class CopilotExplanationResponse(BaseModel):
    """Response schema for copilot explanations."""
    region_id: int
    region_name: str
    date: str
    risk_tier: str
    explanation: str

