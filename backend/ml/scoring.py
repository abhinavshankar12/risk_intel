"""Risk scoring pipeline with spatial and temporal smoothing.

Implements the mathematical model:

R_{i,t} = alpha * p_{i,t} + beta * avg_neighbor_p_{i,t} + gamma * R_{i,t-1} + delta * B_i

Where:
- p_{i,t} is the raw model prediction for region i at time t
- avg_neighbor_p_{i,t} is the average of neighbor predictions
- R_{i,t-1} is the previous smoothed risk score
- B_i is the baseline risk index
- alpha, beta, gamma, delta are configurable weights

Risk tiers are assigned based on thresholds:
- high: R_{i,t} >= theta_high
- medium: theta_medium <= R_{i,t} < theta_high
- low: R_{i,t} < theta_medium
"""
import os
from datetime import datetime, timedelta, date as date_type
from typing import Dict, List, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.db.models import (
    Region, RegionFeature, RegionNeighbor, RiskScore, AuditLog
)
from backend.ml.utils import load_active_model, get_risk_tier


class RiskScorer:
    """Computes risk scores with spatial and temporal smoothing."""
    
    def __init__(
        self,
        db: Session,
        alpha: float = 0.4,
        beta: float = 0.2,
        gamma: float = 0.3,
        delta: float = 0.1,
        theta_high: float = 0.7,
        theta_medium: float = 0.4
    ):
        """Initialize risk scorer.
        
        Args:
            db: Database session
            alpha: Weight for current model prediction
            beta: Weight for neighbor average
            gamma: Weight for temporal smoothing (previous day)
            delta: Weight for baseline risk
            theta_high: Threshold for high risk tier
            theta_medium: Threshold for medium risk tier
        """
        self.db = db
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.theta_high = theta_high
        self.theta_medium = theta_medium
        
        # Validate weights
        weight_sum = alpha + beta + gamma + delta
        if weight_sum > 1.0 + 1e-6:  # Allow small floating point error
            raise ValueError(
                f"Weights sum to {weight_sum}, which exceeds 1.0. "
                "This may cause instability."
            )
    
    def compute_raw_predictions(
        self,
        model,
        feature_columns: List[str],
        target_date: date_type
    ) -> Dict[int, float]:
        """Compute raw model predictions p_{i,t} for all regions.
        
        Args:
            model: Trained ML model
            feature_columns: List of feature column names
            target_date: Date to compute predictions for
            
        Returns:
            Dictionary mapping region_id to p_{i,t}
        """
        # Load features for target date
        features = self.db.query(RegionFeature).filter(
            RegionFeature.date == target_date
        ).all()
        
        if not features:
            raise ValueError(f"No features found for date {target_date}")
        
        predictions = {}
        
        for feature in features:
            # Extract feature values in the correct order
            feature_values = np.array([
                [getattr(feature, col) for col in feature_columns]
            ])
            
            # Get probability of positive class (incident in prediction window)
            p_raw = model.predict_proba(feature_values)[0, 1]
            predictions[feature.region_id] = float(p_raw)
        
        return predictions
    
    def compute_neighbor_averages(
        self,
        raw_predictions: Dict[int, float]
    ) -> Dict[int, float]:
        """Compute average neighbor predictions for all regions.
        
        avg_neighbor_p_{i,t} = (1 / |N(i)|) * sum_{j in N(i)} p_{j,t}
        
        Args:
            raw_predictions: Dictionary of region_id -> p_{i,t}
            
        Returns:
            Dictionary mapping region_id to avg_neighbor_p_{i,t}
        """
        neighbor_averages = {}
        
        for region_id in raw_predictions.keys():
            # Get neighbors
            neighbors = self.db.query(RegionNeighbor).filter(
                RegionNeighbor.region_id == region_id
            ).all()
            
            if not neighbors:
                # No neighbors, use zero
                neighbor_averages[region_id] = 0.0
            else:
                # Compute weighted average
                total_weight = 0.0
                weighted_sum = 0.0
                
                for neighbor in neighbors:
                    neighbor_id = neighbor.neighbor_id
                    weight = neighbor.weight
                    
                    if neighbor_id in raw_predictions:
                        weighted_sum += weight * raw_predictions[neighbor_id]
                        total_weight += weight
                
                if total_weight > 0:
                    neighbor_averages[region_id] = weighted_sum / total_weight
                else:
                    neighbor_averages[region_id] = 0.0
        
        return neighbor_averages
    
    def get_previous_smoothed_scores(
        self,
        target_date: date_type
    ) -> Dict[int, float]:
        """Get previous day's smoothed risk scores R_{i,t-1}.
        
        Args:
            target_date: Current date
            
        Returns:
            Dictionary mapping region_id to R_{i,t-1}
        """
        prev_date = target_date - timedelta(days=1)
        
        prev_scores = self.db.query(RiskScore).filter(
            RiskScore.date == prev_date
        ).all()
        
        return {score.region_id: score.r_smoothed for score in prev_scores}
    
    def compute_smoothed_scores(
        self,
        raw_predictions: Dict[int, float],
        neighbor_averages: Dict[int, float],
        previous_scores: Dict[int, float],
        baseline_risks: Dict[int, float]
    ) -> Dict[int, Tuple[float, str]]:
        """Compute smoothed risk scores and tiers for all regions.
        
        R_{i,t} = alpha * p_{i,t} + beta * avg_neighbor_p_{i,t} + gamma * R_{i,t-1} + delta * B_i
        
        Args:
            raw_predictions: Dictionary of p_{i,t}
            neighbor_averages: Dictionary of avg_neighbor_p_{i,t}
            previous_scores: Dictionary of R_{i,t-1}
            baseline_risks: Dictionary of B_i
            
        Returns:
            Dictionary mapping region_id to (R_{i,t}, risk_tier)
        """
        smoothed_scores = {}
        
        for region_id in raw_predictions.keys():
            p_raw = raw_predictions[region_id]
            neighbor_avg = neighbor_averages.get(region_id, 0.0)
            prev_r = previous_scores.get(region_id, 0.0)
            baseline = baseline_risks.get(region_id, 0.0)
            
            # Apply smoothing formula
            r_smoothed = (
                self.alpha * p_raw +
                self.beta * neighbor_avg +
                self.gamma * prev_r +
                self.delta * baseline
            )
            
            # Classify into risk tier
            risk_tier = get_risk_tier(r_smoothed, self.theta_high, self.theta_medium)
            
            smoothed_scores[region_id] = (r_smoothed, risk_tier)
        
        return smoothed_scores
    
    def save_risk_scores(
        self,
        target_date: date_type,
        raw_predictions: Dict[int, float],
        neighbor_averages: Dict[int, float],
        previous_scores: Dict[int, float],
        smoothed_scores: Dict[int, Tuple[float, str]],
        model_version: str
    ) -> List[RiskScore]:
        """Save computed risk scores to database.
        
        Args:
            target_date: Date scores were computed for
            raw_predictions: Raw model predictions
            neighbor_averages: Neighbor averages
            previous_scores: Previous smoothed scores
            smoothed_scores: Final smoothed scores and tiers
            model_version: Model version used
            
        Returns:
            List of saved RiskScore objects
        """
        saved_scores = []
        
        for region_id, (r_smoothed, risk_tier) in smoothed_scores.items():
            score = RiskScore(
                region_id=region_id,
                date=target_date,
                p_raw=raw_predictions[region_id],
                r_smoothed=r_smoothed,
                risk_tier=risk_tier,
                model_version=model_version,
                neighbor_avg_p=neighbor_averages.get(region_id),
                prev_r=previous_scores.get(region_id),
            )
            self.db.add(score)
            saved_scores.append(score)
        
        self.db.commit()
        
        return saved_scores
    
    def score_date(
        self,
        target_date: date_type,
        actor: str = "system"
    ) -> List[RiskScore]:
        """Main scoring pipeline for a given date.
        
        Args:
            target_date: Date to compute scores for
            actor: Who is running the scoring
            
        Returns:
            List of saved RiskScore objects
        """
        # Load active model
        model, model_record = load_active_model(self.db)
        feature_columns = model_record.config_json.get("feature_columns", [])
        
        # Step 1: Compute raw predictions p_{i,t}
        print(f"Computing raw predictions for {target_date}...")
        raw_predictions = self.compute_raw_predictions(
            model, feature_columns, target_date
        )
        
        # Step 2: Compute neighbor averages
        print("Computing neighbor averages...")
        neighbor_averages = self.compute_neighbor_averages(raw_predictions)
        
        # Step 3: Get previous smoothed scores R_{i,t-1}
        print("Loading previous smoothed scores...")
        previous_scores = self.get_previous_smoothed_scores(target_date)
        
        # Step 4: Get baseline risks
        regions = self.db.query(Region).all()
        baseline_risks = {r.region_id: r.baseline_risk for r in regions}
        
        # Step 5: Compute smoothed scores and risk tiers
        print("Computing smoothed scores...")
        smoothed_scores = self.compute_smoothed_scores(
            raw_predictions,
            neighbor_averages,
            previous_scores,
            baseline_risks
        )
        
        # Step 6: Save to database
        print("Saving risk scores...")
        saved_scores = self.save_risk_scores(
            target_date,
            raw_predictions,
            neighbor_averages,
            previous_scores,
            smoothed_scores,
            model_record.model_version
        )
        
        # Step 7: Audit log
        tier_counts = {
            "high": sum(1 for _, tier in smoothed_scores.values() if tier == "high"),
            "medium": sum(1 for _, tier in smoothed_scores.values() if tier == "medium"),
            "low": sum(1 for _, tier in smoothed_scores.values() if tier == "low"),
        }
        
        audit = AuditLog(
            actor=actor,
            action_type="scores_computed",
            payload_json={
                "date": target_date.isoformat(),
                "model_version": model_record.model_version,
                "regions_scored": len(smoothed_scores),
                "tier_counts": tier_counts,
            }
        )
        self.db.add(audit)
        self.db.commit()
        
        print(f"Scoring complete: {len(saved_scores)} regions scored")
        print(f"Tier distribution: {tier_counts}")
        
        return saved_scores


def score_regions_for_date(
    db: Session,
    target_date: date_type,
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    gamma: Optional[float] = None,
    delta: Optional[float] = None,
    theta_high: Optional[float] = None,
    theta_medium: Optional[float] = None,
    actor: str = "system"
) -> List[RiskScore]:
    """Main entry point for risk scoring.
    
    Args:
        db: Database session
        target_date: Date to compute scores for
        alpha: Weight for current prediction (default from env)
        beta: Weight for neighbor average (default from env)
        gamma: Weight for temporal smoothing (default from env)
        delta: Weight for baseline risk (default from env)
        theta_high: High risk threshold (default from env)
        theta_medium: Medium risk threshold (default from env)
        actor: Who is running the scoring
        
    Returns:
        List of saved RiskScore objects
    """
    # Load parameters from environment if not provided
    if alpha is None:
        alpha = float(os.getenv("ALPHA", "0.4"))
    if beta is None:
        beta = float(os.getenv("BETA", "0.2"))
    if gamma is None:
        gamma = float(os.getenv("GAMMA", "0.3"))
    if delta is None:
        delta = float(os.getenv("DELTA", "0.1"))
    if theta_high is None:
        theta_high = float(os.getenv("THETA_HIGH", "0.7"))
    if theta_medium is None:
        theta_medium = float(os.getenv("THETA_MEDIUM", "0.4"))
    
    scorer = RiskScorer(
        db=db,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        delta=delta,
        theta_high=theta_high,
        theta_medium=theta_medium
    )
    
    return scorer.score_date(target_date, actor=actor)

