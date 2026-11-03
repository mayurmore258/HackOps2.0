"""
THERMOS AI - AI/ML Model Registry, Training Runs, and Predictions
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.db.base import Base, UUIDMixin, TimestampMixin


class ModelRegistry(Base, UUIDMixin, TimestampMixin):
    """Registry of trained environmental forecasting and regression models."""
    __tablename__ = "model_registry"

    model_name = Column(String(100), unique=True, nullable=False, index=True)
    model_type = Column(String(50), default="regression", nullable=False)  # regression, time_series, classification
    algorithm = Column(String(50), nullable=False)  # RandomForestRegressor, XGBRegressor
    version = Column(String(30), default="1.0.0", nullable=False)
    target_variable = Column(String(50), nullable=False)  # lst_celsius, nox_emission, composite_risk
    input_features = Column(JSON, nullable=False)
    artifact_path = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Validation Performance on Held-Out Test Set
    test_mae = Column(Float, nullable=True)
    test_rmse = Column(Float, nullable=True)
    test_r2 = Column(Float, nullable=True)
    split_strategy = Column(String(100), default="spatial_and_temporal_holdout", nullable=False)

    training_runs = relationship("ModelTrainingRun", back_populates="model", cascade="all, delete-orphan")
    predictions = relationship("EnvironmentalPrediction", back_populates="model")


class ModelTrainingRun(Base, UUIDMixin, TimestampMixin):
    """Historical record of model training and evaluation runs."""
    __tablename__ = "model_training_runs"

    model_id = Column(UUIDMixin.id.type, ForeignKey("model_registry.id", ondelete="CASCADE"), nullable=False, index=True)
    trained_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    train_samples = Column(Integer, nullable=False)
    test_samples = Column(Integer, nullable=False)
    hyperparameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=False)  # mae, rmse, r2, feature_importance
    training_duration_sec = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    model = relationship("ModelRegistry", back_populates="training_runs")


class EnvironmentalPrediction(Base, UUIDMixin, TimestampMixin):
    """Generated forecast outputs with confidence intervals and explainability."""
    __tablename__ = "environmental_predictions"

    model_id = Column(UUIDMixin.id.type, ForeignKey("model_registry.id", ondelete="CASCADE"), nullable=False, index=True)
    target_variable = Column(String(50), nullable=False, index=True)
    prediction_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    horizon = Column(String(50), default="seasonal_estimate", nullable=False)
    predicted_value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    input_features_snapshot = Column(JSON, nullable=False)
    explanation_json = Column(JSON, nullable=True)  # Feature contribution / SHAP approximations
    data_classification = Column(String(30), default="modelled", nullable=False)
    limitations = Column(Text, nullable=False)

    model = relationship("ModelRegistry", back_populates="predictions")

