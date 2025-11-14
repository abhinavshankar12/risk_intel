"""SQLAlchemy database models for risk intelligence platform.

All models strictly adhere to privacy and civil rights constraints:
- No religion, ethnicity, immigration status, or political opinion fields
- Only concrete behavior, incident data, and structural risk factors
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean, Text, JSON,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from backend.db.base import Base


class Region(Base):
    """Geographic regions for risk analysis."""
    __tablename__ = "regions"
    
    region_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    # Geometry for spatial operations (optional, can use simple lat/lon if needed)
    geom = Column(Geometry("POLYGON", srid=4326), nullable=True)
    # Baseline risk: normalized structural risk index (0-1)
    # Based on: critical infrastructure presence, long-term historical incident rates
    baseline_risk = Column(Float, nullable=False, default=0.0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    incidents = relationship("Incident", back_populates="region")
    events = relationship("Event", back_populates="region")
    risk_scores = relationship("RiskScore", back_populates="region")
    features = relationship("RegionFeature", back_populates="region")
    content_signals = relationship("ContentSignal", back_populates="region")
    
    __table_args__ = (
        CheckConstraint("baseline_risk >= 0 AND baseline_risk <= 1", name="baseline_risk_range"),
    )


class RegionNeighbor(Base):
    """Adjacency relationships between regions for spatial smoothing."""
    __tablename__ = "region_neighbors"
    
    region_id = Column(Integer, ForeignKey("regions.region_id"), primary_key=True)
    neighbor_id = Column(Integer, ForeignKey("regions.region_id"), primary_key=True)
    
    # Optional: distance or weight for weighted averaging
    weight = Column(Float, default=1.0)
    
    __table_args__ = (
        Index("idx_region_neighbors_region", "region_id"),
        Index("idx_region_neighbors_neighbor", "neighbor_id"),
    )


class Incident(Base):
    """Legally defined violent extremist incidents.
    
    Strictly based on:
    - Confirmed violent acts or explicit threats
    - Law enforcement records
    - No profiling based on protected characteristics
    """
    __tablename__ = "incidents"
    
    incident_id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    
    # When the incident occurred
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    
    # Type: e.g., "assault", "threat", "vandalism", "weapons_offense"
    type = Column(String(100), nullable=False)
    
    # Severity: normalized 0-1 or categorical (low, medium, high, critical)
    severity = Column(Float, nullable=False, default=0.5)
    
    # Source: e.g., "law_enforcement", "verified_report"
    source = Column(String(100), nullable=False)
    
    # Optional: additional structured data
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    region = relationship("Region", back_populates="incidents")
    
    __table_args__ = (
        Index("idx_incidents_region_occurred", "region_id", "occurred_at"),
        CheckConstraint("severity >= 0 AND severity <= 1", name="severity_range"),
    )


class Event(Base):
    """Public events that may be targets or catalysts.
    
    Examples: large gatherings, critical infrastructure events, public ceremonies.
    No tracking of religious, ethnic, or political identity of attendees.
    """
    __tablename__ = "events"
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Type: e.g., "large_gathering", "infrastructure_event", "public_ceremony"
    type = Column(String(100), nullable=False)
    
    # Expected attendance (if known)
    expected_attendance = Column(Integer, nullable=True)
    
    # Optional metadata
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    region = relationship("Region", back_populates="events")
    
    __table_args__ = (
        Index("idx_events_region_start", "region_id", "start_time"),
    )


class ContentSignal(Base):
    """Aggregated counts of explicit violence calls from content analysis.
    
    Strictly focused on:
    - Explicit calls for physical violence
    - Direct threats of harm
    - NOT generic anger, frustration, or protected speech
    
    All content analysis uses strict prompts that avoid bias.
    """
    __tablename__ = "content_signals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Count of posts with explicit calls for physical violence
    violent_call_post_count = Column(Integer, nullable=False, default=0)
    
    # Optional: additional signal counts
    # threat_count, weapon_mention_count, etc.
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    region = relationship("Region", back_populates="content_signals")
    
    __table_args__ = (
        Index("idx_content_signals_region_date", "region_id", "date", unique=True),
    )


class RegionFeature(Base):
    """Computed features for each region and date for ML model input."""
    __tablename__ = "region_features"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Incident-based features
    recent_incidents_7d = Column(Integer, nullable=False, default=0)
    recent_incidents_30d = Column(Integer, nullable=False, default=0)
    neighbor_incidents_7d = Column(Integer, nullable=False, default=0)
    neighbor_incidents_30d = Column(Integer, nullable=False, default=0)
    
    # Event-based features
    event_count_7d = Column(Integer, nullable=False, default=0)
    event_attendance_7d = Column(Integer, nullable=False, default=0)
    
    # Content-based features
    content_violent_count = Column(Integer, nullable=False, default=0)
    
    # Baseline risk (denormalized from regions for easier ML pipeline)
    baseline_risk = Column(Float, nullable=False, default=0.0)
    
    # Optional: additional computed features
    features_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    region = relationship("Region", back_populates="features")
    
    __table_args__ = (
        Index("idx_region_features_region_date", "region_id", "date", unique=True),
    )


class RiskScore(Base):
    """Computed risk scores for each region and date.
    
    Includes:
    - Raw model prediction p_{i,t}
    - Smoothed risk score R_{i,t}
    - Risk tier classification
    """
    __tablename__ = "risk_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(Integer, ForeignKey("regions.region_id"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Raw model prediction probability
    p_raw = Column(Float, nullable=False)
    
    # Smoothed risk score R_{i,t}
    r_smoothed = Column(Float, nullable=False)
    
    # Risk tier: "low", "medium", "high"
    risk_tier = Column(String(20), nullable=False)
    
    # Model version used for this score
    model_version = Column(String(50), nullable=False)
    
    # Optional: store smoothing components for debugging
    neighbor_avg_p = Column(Float, nullable=True)
    prev_r = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    region = relationship("Region", back_populates="risk_scores")
    
    __table_args__ = (
        Index("idx_risk_scores_region_date", "region_id", "date"),
        Index("idx_risk_scores_date", "date"),
        CheckConstraint("p_raw >= 0 AND p_raw <= 1", name="p_raw_range"),
        CheckConstraint("r_smoothed >= 0", name="r_smoothed_positive"),
        CheckConstraint("risk_tier IN ('low', 'medium', 'high')", name="risk_tier_values"),
    )


class Model(Base):
    """Model registry for ML model versioning and metadata."""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_version = Column(String(50), nullable=False, unique=True)
    
    # When the model was trained
    trained_at = Column(DateTime(timezone=True), nullable=False)
    
    # Algorithm: "logistic_regression", "xgboost", "lightgbm", etc.
    algorithm = Column(String(50), nullable=False)
    
    # Evaluation metrics as JSON: {"auc": 0.85, "precision": 0.72, "recall": 0.68}
    metrics_json = Column(JSON, nullable=False)
    
    # Is this the currently active model?
    active_flag = Column(Boolean, nullable=False, default=False)
    
    # Optional: hyperparameters, feature names, etc.
    config_json = Column(JSON, nullable=True)
    
    # File path to serialized model
    model_path = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_models_active", "active_flag"),
    )


class AuditLog(Base):
    """Audit trail for all model training, scoring, and data operations.
    
    Required for governance and accountability.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Actor: user_id, service name, or "system"
    actor = Column(String(100), nullable=False)
    
    # Action type: "model_trained", "score_computed", "data_ingested", etc.
    action_type = Column(String(100), nullable=False)
    
    # Payload: structured data about the action
    payload_json = Column(JSON, nullable=False)
    
    __table_args__ = (
        Index("idx_audit_logs_created", "created_at"),
        Index("idx_audit_logs_action", "action_type"),
    )

