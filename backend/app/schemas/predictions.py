"""
THERMOS AI - AI/ML Environmental Predictions Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str
    model_name: str
    model_type: str
    algorithm: str
    version: str
    target_variable: str
    input_features: List[str]
    is_active: bool
    test_mae: Optional[float] = None
    test_rmse: Optional[float] = None
    test_r2: Optional[float] = None
    split_strategy: str


class PredictionItem(BaseModel):
    id: str
    model_name: str
    model_version: str
    target_variable: str
    horizon: str
    predicted_value: float
    unit: str
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    prediction_timestamp: str
    data_classification: str
    input_features_snapshot: Dict[str, Any]
    explanation: Optional[Dict[str, Any]] = None
    limitations: str


class PredictionSummaryResponse(BaseModel):
    available_models: List[ModelInfo]
    recent_predictions: List[PredictionItem]
    model_readiness_status: str
    limitations: str


class PredictionRunRequest(BaseModel):
    target_variable: str = Field(default="lst_celsius", description="Target variable to predict (e.g. lst_celsius)")
    horizon: str = Field(default="next_period", description="Forecast horizon")
    input_features: Dict[str, float] = Field(
        ...,
        description="Dictionary of input feature values (e.g., {'ndvi': 0.15, 'ndbi': 0.35, 'day_of_year': 120, 'solar_radiation': 850.0})"
    )
    algorithm: Optional[str] = Field(default="RandomForest", description="RandomForest or XGBoost")

