"""Main FastAPI application."""
import os
from datetime import date as date_type, datetime
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from dotenv import load_dotenv

from backend.db.base import get_db
from backend.db.models import Region, RiskScore, Incident, Model, AuditLog
from backend.api.schemas import (
    RegionResponse, RiskScoreResponse, IncidentResponse,
    ModelResponse, AuditLogResponse, CopilotExplanationResponse
)
from backend.copilot.explainer import CopilotExplainer

load_dotenv()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Risk Intelligence Platform API",
        description="API for violent extremism hotspot risk prediction with privacy and civil rights guardrails",
        version="1.0.0"
    )
    
    # CORS configuration
    origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    
    # ========== REGION ENDPOINTS ==========
    
    @app.get("/api/regions", response_model=List[RegionResponse])
    def get_regions(
        db: Session = Depends(get_db)
    ):
        """Get all regions."""
        regions = db.query(Region).all()
        return regions
    
    @app.get("/api/regions/{region_id}", response_model=RegionResponse)
    def get_region(
        region_id: int,
        db: Session = Depends(get_db)
    ):
        """Get a specific region."""
        region = db.query(Region).filter(Region.region_id == region_id).first()
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        return region
    
    # ========== RISK SCORE ENDPOINTS ==========
    
    @app.get("/api/risk_scores", response_model=List[RiskScoreResponse])
    def get_risk_scores(
        date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
        risk_tier: Optional[str] = Query(None, description="Filter by risk tier: low, medium, high"),
        db: Session = Depends(get_db)
    ):
        """Get risk scores, optionally filtered by date and/or risk tier."""
        query = db.query(RiskScore)
        
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                query = query.filter(RiskScore.date == target_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        if risk_tier:
            if risk_tier not in ["low", "medium", "high"]:
                raise HTTPException(status_code=400, detail="risk_tier must be low, medium, or high")
            query = query.filter(RiskScore.risk_tier == risk_tier)
        
        scores = query.order_by(desc(RiskScore.r_smoothed)).all()
        return scores
    
    @app.get("/api/regions/{region_id}/risk_history", response_model=List[RiskScoreResponse])
    def get_region_risk_history(
        region_id: int,
        start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
        end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
        limit: int = Query(30, ge=1, le=365, description="Number of days to return"),
        db: Session = Depends(get_db)
    ):
        """Get risk score history for a specific region."""
        # Verify region exists
        region = db.query(Region).filter(Region.region_id == region_id).first()
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        
        query = db.query(RiskScore).filter(RiskScore.region_id == region_id)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(RiskScore.date >= start)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(RiskScore.date <= end)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        scores = query.order_by(desc(RiskScore.date)).limit(limit).all()
        return scores
    
    # ========== INCIDENT ENDPOINTS ==========
    
    @app.get("/api/regions/{region_id}/recent_incidents", response_model=List[IncidentResponse])
    def get_recent_incidents(
        region_id: int,
        limit: int = Query(10, ge=1, le=100, description="Number of incidents to return"),
        db: Session = Depends(get_db)
    ):
        """Get recent incidents for a specific region."""
        # Verify region exists
        region = db.query(Region).filter(Region.region_id == region_id).first()
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        
        incidents = db.query(Incident).filter(
            Incident.region_id == region_id
        ).order_by(desc(Incident.occurred_at)).limit(limit).all()
        
        return incidents
    
    # ========== COPILOT ENDPOINTS ==========
    
    @app.get("/api/copilot/explain_hotspot", response_model=CopilotExplanationResponse)
    def explain_hotspot(
        region_id: int = Query(..., description="Region ID to explain"),
        date: str = Query(..., description="Date in YYYY-MM-DD format"),
        db: Session = Depends(get_db)
    ):
        """Get AI-generated explanation for a region's risk score."""
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Verify region exists
        region = db.query(Region).filter(Region.region_id == region_id).first()
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        
        # Check if risk score exists for this date
        risk_score = db.query(RiskScore).filter(
            and_(
                RiskScore.region_id == region_id,
                RiskScore.date == target_date
            )
        ).first()
        
        if not risk_score:
            raise HTTPException(
                status_code=404,
                detail=f"No risk score found for region {region_id} on {date}"
            )
        
        try:
            explainer = CopilotExplainer()
            explanation = explainer.explain_hotspot(db, region_id, target_date)
            
            return CopilotExplanationResponse(
                region_id=region_id,
                region_name=region.name,
                date=date,
                risk_tier=risk_score.risk_tier,
                explanation=explanation
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")
    
    # ========== MODEL ENDPOINTS ==========
    
    @app.get("/api/models/active", response_model=ModelResponse)
    def get_active_model(
        db: Session = Depends(get_db)
    ):
        """Get the currently active model."""
        model = db.query(Model).filter(Model.active_flag == True).first()  # noqa: E712
        if not model:
            raise HTTPException(status_code=404, detail="No active model found")
        return model
    
    @app.get("/api/models", response_model=List[ModelResponse])
    def get_models(
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db)
    ):
        """Get all models, most recent first."""
        models = db.query(Model).order_by(desc(Model.trained_at)).limit(limit).all()
        return models
    
    # ========== AUDIT LOG ENDPOINTS ==========
    
    @app.get("/api/audit/logs", response_model=List[AuditLogResponse])
    def get_audit_logs(
        action_type: Optional[str] = Query(None, description="Filter by action type"),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db)
    ):
        """Get audit logs (admin only in production - add auth middleware)."""
        query = db.query(AuditLog)
        
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        
        logs = query.order_by(desc(AuditLog.created_at)).limit(limit).all()
        return logs
    
    return app


# Create app instance for uvicorn
app = create_app()

