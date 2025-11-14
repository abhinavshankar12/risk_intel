"""Model training pipeline for hotspot prediction.

Implements:
1. Logistic Regression as baseline
2. XGBoost/LightGBM as main production model

Label definition:
y_{i,t} = 1 if at least one incident occurs in the prediction window, 0 otherwise
"""
from datetime import datetime, timedelta, date as date_type
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.db.models import RegionFeature, Incident, Model, AuditLog
from backend.ml.utils import save_model


class ModelTrainer:
    """Trains risk prediction models."""
    
    FEATURE_COLUMNS = [
        "recent_incidents_7d",
        "recent_incidents_30d",
        "neighbor_incidents_7d",
        "neighbor_incidents_30d",
        "event_count_7d",
        "event_attendance_7d",
        "content_violent_count",
        "baseline_risk",
    ]
    
    def __init__(self, db: Session, prediction_window_days: int = 7):
        """Initialize trainer.
        
        Args:
            db: Database session
            prediction_window_days: Days to look ahead for incident labels
        """
        self.db = db
        self.prediction_window_days = prediction_window_days
    
    def build_training_dataset(
        self,
        start_date: date_type,
        end_date: date_type
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """Build labeled training dataset from region_features and incidents.
        
        Args:
            start_date: Start date for training data
            end_date: End date for training data
            
        Returns:
            Tuple of (features_df, labels_array)
        """
        # Load all features in date range
        features = self.db.query(RegionFeature).filter(
            and_(
                RegionFeature.date >= start_date,
                RegionFeature.date <= end_date
            )
        ).all()
        
        if not features:
            raise ValueError("No features found for the given date range")
        
        # Build feature matrix
        feature_rows = []
        labels = []
        
        for feature in features:
            # Extract feature values
            feature_dict = {col: getattr(feature, col) for col in self.FEATURE_COLUMNS}
            feature_dict["region_id"] = feature.region_id
            feature_dict["date"] = feature.date
            feature_rows.append(feature_dict)
            
            # Compute label: did any incident occur in prediction window?
            label = self._compute_label(feature.region_id, feature.date)
            labels.append(label)
        
        features_df = pd.DataFrame(feature_rows)
        labels_array = np.array(labels)
        
        return features_df, labels_array
    
    def _compute_label(self, region_id: int, feature_date: date_type) -> int:
        """Compute label for a region and date.
        
        Label is 1 if at least one incident occurs in the prediction window, 0 otherwise.
        
        Args:
            region_id: Region ID
            feature_date: Date when features were computed
            
        Returns:
            Binary label (0 or 1)
        """
        window_start = datetime.combine(feature_date, datetime.min.time())
        window_end = window_start + timedelta(days=self.prediction_window_days)
        
        # Check if any incidents occurred in the prediction window
        count = self.db.query(Incident).filter(
            and_(
                Incident.region_id == region_id,
                Incident.occurred_at >= window_start,
                Incident.occurred_at < window_end
            )
        ).count()
        
        return 1 if count > 0 else 0
    
    def train_logistic_regression(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[LogisticRegression, Dict]:
        """Train logistic regression baseline model.
        
        Args:
            X: Feature matrix
            y: Labels
            test_size: Proportion for test split
            random_state: Random seed
            
        Returns:
            Tuple of (trained_model, metrics_dict)
        """
        # Use only feature columns for training
        X_train, X_test, y_train, y_test = train_test_split(
            X[self.FEATURE_COLUMNS], y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Train model
        model = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        metrics = self._evaluate_model(model, X_test, y_test)
        
        return model, metrics
    
    def train_xgboost(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[XGBClassifier, Dict]:
        """Train XGBoost model.
        
        Args:
            X: Feature matrix
            y: Labels
            test_size: Proportion for test split
            random_state: Random seed
            
        Returns:
            Tuple of (trained_model, metrics_dict)
        """
        X_train, X_test, y_train, y_test = train_test_split(
            X[self.FEATURE_COLUMNS], y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Calculate scale_pos_weight for imbalanced classes
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
        
        model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            random_state=random_state,
            eval_metric="logloss"
        )
        model.fit(X_train, y_train)
        
        metrics = self._evaluate_model(model, X_test, y_test)
        
        return model, metrics
    
    def train_lightgbm(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[LGBMClassifier, Dict]:
        """Train LightGBM model.
        
        Args:
            X: Feature matrix
            y: Labels
            test_size: Proportion for test split
            random_state: Random seed
            
        Returns:
            Tuple of (trained_model, metrics_dict)
        """
        X_train, X_test, y_train, y_test = train_test_split(
            X[self.FEATURE_COLUMNS], y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        model = LGBMClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            class_weight="balanced",
            random_state=random_state,
            verbose=-1
        )
        model.fit(X_train, y_train)
        
        metrics = self._evaluate_model(model, X_test, y_test)
        
        return model, metrics
    
    def _evaluate_model(self, model, X_test, y_test) -> Dict:
        """Evaluate model and return metrics.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary of metrics
        """
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        metrics = {
            "auc": float(roc_auc_score(y_test, y_proba)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "test_samples": len(y_test),
            "positive_samples": int((y_test == 1).sum()),
            "negative_samples": int((y_test == 0).sum()),
        }
        
        return metrics
    
    def save_model_to_registry(
        self,
        model,
        model_version: str,
        algorithm: str,
        metrics: Dict,
        model_path: str,
        set_active: bool = False,
        actor: str = "system"
    ) -> Model:
        """Save model to database registry and disk.
        
        Args:
            model: Trained model object
            model_version: Version string
            algorithm: Algorithm name
            metrics: Evaluation metrics
            model_path: Path to save model file
            set_active: Whether to set as active model
            actor: Who is saving the model
            
        Returns:
            Model database record
        """
        # Save model to disk
        save_model(model, model_path)
        
        # If setting as active, deactivate all other models
        if set_active:
            self.db.query(Model).update({"active_flag": False})
        
        # Create model record
        model_record = Model(
            model_version=model_version,
            trained_at=datetime.utcnow(),
            algorithm=algorithm,
            metrics_json=metrics,
            active_flag=set_active,
            model_path=model_path,
            config_json={
                "feature_columns": self.FEATURE_COLUMNS,
                "prediction_window_days": self.prediction_window_days,
            }
        )
        
        self.db.add(model_record)
        self.db.commit()
        self.db.refresh(model_record)
        
        # Log to audit trail
        audit = AuditLog(
            actor=actor,
            action_type="model_trained",
            payload_json={
                "model_version": model_version,
                "algorithm": algorithm,
                "metrics": metrics,
                "active": set_active,
            }
        )
        self.db.add(audit)
        self.db.commit()
        
        return model_record


def train_model(
    db: Session,
    algorithm: str = "logistic_regression",
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    model_version: Optional[str] = None,
    set_active: bool = True,
    actor: str = "system"
) -> Model:
    """Main entry point for model training.
    
    Args:
        db: Database session
        algorithm: "logistic_regression", "xgboost", or "lightgbm"
        start_date: Start date for training data
        end_date: End date for training data
        model_version: Version string (auto-generated if None)
        set_active: Whether to set as active model
        actor: Who is training the model
        
    Returns:
        Model database record
    """
    # Set default dates if not provided
    if end_date is None:
        end_date = datetime.utcnow().date()
    if start_date is None:
        start_date = end_date - timedelta(days=90)  # 90 days of training data
    
    # Generate model version if not provided
    if model_version is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_version = f"{algorithm}_{timestamp}"
    
    trainer = ModelTrainer(db)
    
    # Build dataset
    print(f"Building training dataset from {start_date} to {end_date}...")
    X, y = trainer.build_training_dataset(start_date, end_date)
    print(f"Dataset: {len(X)} samples, {y.sum()} positive labels")
    
    # Train model based on algorithm
    print(f"Training {algorithm} model...")
    if algorithm == "logistic_regression":
        model, metrics = trainer.train_logistic_regression(X, y)
    elif algorithm == "xgboost":
        model, metrics = trainer.train_xgboost(X, y)
    elif algorithm == "lightgbm":
        model, metrics = trainer.train_lightgbm(X, y)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    print(f"Training complete. Metrics: {metrics}")
    
    # Save model
    model_path = f"./models/{model_version}.joblib"
    model_record = trainer.save_model_to_registry(
        model=model,
        model_version=model_version,
        algorithm=algorithm,
        metrics=metrics,
        model_path=model_path,
        set_active=set_active,
        actor=actor
    )
    
    print(f"Model saved: {model_version} (active={set_active})")
    
    return model_record

