"""
THERMOS AI - AI/ML Environmental Predictions API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.ml import ModelRegistry, EnvironmentalPrediction
from ml.inference.predictor import LSTPredictor
from app.schemas.common import ResponseEnvelope, ResponseMetadata
from app.schemas.predictions import (
    ModelInfo,
    PredictionItem,
    PredictionSummaryResponse,
    PredictionRunRequest,
)

router = APIRouter(prefix="/predictions", tags=["AI/ML Environmental Predictions"])


@router.get("/summary", response_model=ResponseEnvelope[PredictionSummaryResponse])
def get_predictions_summary(db: Session = Depends(get_db)):
    """Retrieve overview of trained machine learning models, validation metrics, and recent predictions."""
    models = db.query(ModelRegistry).filter(ModelRegistry.is_active == True).all()
    model_infos = [
        ModelInfo(
            id=str(m.id),
            model_name=m.model_name,
            model_type=m.model_type,
            algorithm=m.algorithm,
            version=m.version,
            target_variable=m.target_variable,
            input_features=m.input_features,
            is_active=m.is_active,
            test_mae=m.test_mae,
            test_rmse=m.test_rmse,
            test_r2=m.test_r2,
            split_strategy=m.split_strategy
        )
        for m in models
    ]
    
    recent_preds = db.query(EnvironmentalPrediction).order_by(EnvironmentalPrediction.prediction_timestamp.desc()).limit(5).all()
    prediction_items = [
        PredictionItem(
            id=str(p.id),
            model_name=p.model.model_name if p.model else "RandomForest_LST",
            model_version=p.model.version if p.model else "1.0.0",
            target_variable=p.target_variable,
            horizon=p.horizon,
            predicted_value=p.predicted_value,
            unit=p.unit,
            lower_bound=p.lower_bound,
            upper_bound=p.upper_bound,
            prediction_timestamp=p.prediction_timestamp.isoformat(),
            data_classification=p.data_classification,
            input_features_snapshot=p.input_features_snapshot,
            explanation=p.explanation_json,
            limitations=p.limitations
        )
        for p in recent_preds
    ]

    return ResponseEnvelope(
        success=True,
        data=PredictionSummaryResponse(
            available_models=model_infos,
            recent_predictions=prediction_items,
            model_readiness_status="Operational (Trained on held-out biophysical dataset)",
            limitations="Statistical machine learning estimates; prediction interval indicates 95% confidence bounds."
        ),
        metadata=ResponseMetadata(
            source="THERMOS AI Model Registry",
            classification="modelled"
        )
    )


@router.get("/models", response_model=ResponseEnvelope[List[ModelInfo]])
def list_models(db: Session = Depends(get_db)):
    """List all registered and evaluated ML models with cross-validation test scores."""
    models = db.query(ModelRegistry).all()
    items = [
        ModelInfo(
            id=str(m.id),
            model_name=m.model_name,
            model_type=m.model_type,
            algorithm=m.algorithm,
            version=m.version,
            target_variable=m.target_variable,
            input_features=m.input_features,
            is_active=m.is_active,
            test_mae=m.test_mae,
            test_rmse=m.test_rmse,
            test_r2=m.test_r2,
            split_strategy=m.split_strategy
        )
        for m in models
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="Model Evaluation Registry", classification="modelled")
    )


@router.get("/heat", response_model=ResponseEnvelope[PredictionItem])
def get_default_heat_prediction():
    """Retrieve sample explainable Land Surface Temperature prediction for representative urban conditions."""
    pred = LSTPredictor.predict(
        {"ndvi": 0.12, "ndbi": 0.42, "solar_radiation": 880.0, "day_of_year": 125.0},
        algorithm="RandomForest"
    )
    item = PredictionItem(
        id="PRED-LST-SAMPLE-01",
        model_name=pred["model_name"],
        model_version=pred["model_version"],
        target_variable=pred["target_variable"],
        horizon="next_seasonal_cycle",
        predicted_value=pred["predicted_value"],
        unit=pred["unit"],
        lower_bound=pred["lower_bound"],
        upper_bound=pred["upper_bound"],
        prediction_timestamp="2026-11-03T12:00:00Z",
        data_classification="modelled",
        input_features_snapshot=pred["input_features"],
        explanation=pred["explanation"],
        limitations=pred["limitations"]
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="Random Forest LST Regressor", classification="modelled")
    )


@router.get("/history", response_model=ResponseEnvelope[List[PredictionItem]])
def list_prediction_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List historical prediction executions."""
    preds = db.query(EnvironmentalPrediction).order_by(EnvironmentalPrediction.prediction_timestamp.desc()).limit(limit).all()
    items = [
        PredictionItem(
            id=str(p.id),
            model_name=p.model.model_name if p.model else "LST_Regressor",
            model_version=p.model.version if p.model else "1.0.0",
            target_variable=p.target_variable,
            horizon=p.horizon,
            predicted_value=p.predicted_value,
            unit=p.unit,
            lower_bound=p.lower_bound,
            upper_bound=p.upper_bound,
            prediction_timestamp=p.prediction_timestamp.isoformat(),
            data_classification=p.data_classification,
            input_features_snapshot=p.input_features_snapshot,
            explanation=p.explanation_json,
            limitations=p.limitations
        )
        for p in preds
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="Prediction Audit Log", classification="modelled")
    )


@router.post("/run", response_model=ResponseEnvelope[PredictionItem])
def run_prediction(
    req: PredictionRunRequest,
    db: Session = Depends(get_db)
):
    """Execute live model inference with custom feature inputs and receive explainable feature contributions."""
    pred = LSTPredictor.predict(req.input_features, algorithm=req.algorithm or "RandomForest")
    
    # Optionally persist prediction
    model_obj = db.query(ModelRegistry).filter(ModelRegistry.algorithm.ilike(f"%{req.algorithm or 'RandomForest'}%")).first()
    if model_obj:
        db_pred = EnvironmentalPrediction(
            model_id=model_obj.id,
            target_variable=req.target_variable,
            horizon=req.horizon,
            predicted_value=pred["predicted_value"],
            unit=pred["unit"],
            lower_bound=pred["lower_bound"],
            upper_bound=pred["upper_bound"],
            input_features_snapshot=pred["input_features"],
            explanation_json=pred["explanation"],
            data_classification="modelled",
            limitations=pred["limitations"]
        )
        db.add(db_pred)
        db.commit()
        db.refresh(db_pred)
        pred_id = str(db_pred.id)
    else:
        pred_id = "PRED-DYNAMIC-01"

    item = PredictionItem(
        id=pred_id,
        model_name=pred["model_name"],
        model_version=pred["model_version"],
        target_variable=pred["target_variable"],
        horizon=req.horizon,
        predicted_value=pred["predicted_value"],
        unit=pred["unit"],
        lower_bound=pred["lower_bound"],
        upper_bound=pred["upper_bound"],
        prediction_timestamp="2026-11-03T12:00:00Z",
        data_classification="modelled",
        input_features_snapshot=pred["input_features"],
        explanation=pred["explanation"],
        limitations=pred["limitations"]
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(
            source=pred["model_name"],
            classification="modelled",
            limitations=[pred["limitations"]]
        )
    )
