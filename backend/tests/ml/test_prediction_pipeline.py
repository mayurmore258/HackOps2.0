"""
Machine Learning and Prediction Inference Tests
"""

import pytest
from ml.inference.predictor import LSTPredictor
from ml.training.trainer import generate_scientific_training_dataset


def test_dataset_generation():
    """Verify synthetic dataset features, ranges, and target variable."""
    df = generate_scientific_training_dataset(n_samples=100)
    assert len(df) == 100
    assert "lst_celsius" in df.columns
    assert "ndvi" in df.columns
    assert "ndbi" in df.columns
    assert "solar_radiation" in df.columns
    assert df["lst_celsius"].min() >= 20.0
    assert df["lst_celsius"].max() <= 55.0


def test_lst_predictor_inference():
    """Verify live inference output, confidence bounds, and explainability."""
    features = {
        "ndvi": 0.15,
        "ndbi": 0.40,
        "ndmi": 0.08,
        "solar_radiation": 850.0,
        "day_of_year": 120.0,
        "impervious_fraction": 0.70
    }
    
    pred = LSTPredictor.predict(features, algorithm="RandomForest")
    assert "predicted_value" in pred
    assert 25.0 <= pred["predicted_value"] <= 48.0
    assert pred["lower_bound"] < pred["predicted_value"] < pred["upper_bound"]
    assert "explanation" in pred
    assert "vegetation_cooling_effect_celsius" in pred["explanation"]
    assert "builtup_thermal_amplification_celsius" in pred["explanation"]


def test_xgboost_inference():
    """Verify XGBoost prediction execution."""
    features = {
        "ndvi": 0.35,
        "ndbi": 0.15,
        "ndmi": 0.20,
        "solar_radiation": 750.0,
        "day_of_year": 200.0,
        "impervious_fraction": 0.30
    }
    pred = LSTPredictor.predict(features, algorithm="XGBoost")
    assert "predicted_value" in pred
    assert pred["predicted_value"] > 0.0

