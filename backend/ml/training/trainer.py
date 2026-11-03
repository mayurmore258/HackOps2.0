"""
THERMOS AI - Machine Learning Training Pipeline

Trains, evaluates, and serializes reproducible Random Forest and XGBoost regression models
for Land Surface Temperature (LST) estimation using spectral and seasonal features.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import xgboost as xgb

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def generate_scientific_training_dataset(n_samples: int = 1500) -> pd.DataFrame:
    """
    Generate physically constrained synthetic training dataset modeling the
    biophysical relationships between surface temperature, vegetation (NDVI),
    built-up density (NDBI), moisture (NDMI), solar angle, and seasonality.
    """
    np.random.seed(settings.ML_RANDOM_STATE)
    
    # Feature 1: Day of Year (1 - 365)
    day_of_year = np.random.randint(1, 366, size=n_samples)
    
    # Feature 2: NDVI (-0.1 to 0.85)
    ndvi = np.random.uniform(-0.05, 0.75, size=n_samples)
    
    # Feature 3: NDBI (-0.5 to 0.6) - inversely related to NDVI
    ndbi = -0.7 * ndvi + np.random.normal(0.1, 0.08, size=n_samples)
    ndbi = np.clip(ndbi, -0.5, 0.6)
    
    # Feature 4: NDMI (-0.3 to 0.5)
    ndmi = 0.5 * ndvi - 0.2 * ndbi + np.random.normal(0.0, 0.05, size=n_samples)
    ndmi = np.clip(ndmi, -0.3, 0.5)
    
    # Feature 5: Solar Radiation Proxy (W/m2, seasonal curve peaking in April/May in India)
    seasonal_rad = 600.0 + 350.0 * np.sin((day_of_year - 40) * 2 * np.pi / 365)
    solar_radiation = np.clip(seasonal_rad + np.random.normal(0, 40, size=n_samples), 250.0, 1050.0)
    
    # Feature 6: Impervious Surface Fraction (0.0 to 1.0)
    impervious_fraction = np.clip((ndbi + 0.5) / 1.1 + np.random.normal(0, 0.05, size=n_samples), 0.0, 1.0)
    
    # Target: LST in Celsius
    base_temp = 28.0 + (solar_radiation - 600.0) * 0.015
    cooling_vegetation = -9.5 * ndvi - 4.0 * ndmi
    heating_builtup = 11.0 * ndbi + 6.0 * impervious_fraction
    noise = np.random.normal(0.0, 0.75, size=n_samples)
    
    lst_celsius = base_temp + cooling_vegetation + heating_builtup + noise
    lst_celsius = np.clip(lst_celsius, 24.0, 50.0)
    
    df = pd.DataFrame({
        "day_of_year": day_of_year,
        "ndvi": np.round(ndvi, 4),
        "ndbi": np.round(ndbi, 4),
        "ndmi": np.round(ndmi, 4),
        "solar_radiation": np.round(solar_radiation, 1),
        "impervious_fraction": np.round(impervious_fraction, 4),
        "lst_celsius": np.round(lst_celsius, 2)
    })
    return df


def train_and_evaluate_models() -> Dict[str, Any]:
    """Train Random Forest and XGBoost models, evaluate on held-out test data, and persist artifacts."""
    logger.info("Generating training dataset for LST prediction...")
    df = generate_scientific_training_dataset(n_samples=2000)
    
    features = ["day_of_year", "ndvi", "ndbi", "ndmi", "solar_radiation", "impervious_fraction"]
    target = "lst_celsius"
    
    X = df[features]
    y = df[target]
    
    # Temporal / held-out split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=settings.ML_TEST_SIZE, random_state=settings.ML_RANDOM_STATE
    )
    
    # 1. Train Random Forest Regressor (n_jobs=1 for Windows safe execution)
    logger.info("Training Random Forest Regressor...")
    rf_model = RandomForestRegressor(
        n_estimators=80,
        max_depth=10,
        min_samples_split=4,
        random_state=settings.ML_RANDOM_STATE,
        n_jobs=1
    )
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    
    rf_mae = float(mean_absolute_error(y_test, y_pred_rf))
    rf_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_rf)))
    rf_r2 = float(r2_score(y_test, y_pred_rf))
    
    # 2. Train XGBoost Regressor (n_jobs=1 for Windows safe execution)
    logger.info("Training XGBoost Regressor...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.08,
        random_state=settings.ML_RANDOM_STATE,
        n_jobs=1
    )
    xgb_model.fit(X_train, y_train)
    y_pred_xgb = xgb_model.predict(X_test)
    
    xgb_mae = float(mean_absolute_error(y_test, y_pred_xgb))
    xgb_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_xgb)))
    xgb_r2 = float(r2_score(y_test, y_pred_xgb))
    
    # Save model artifacts
    artifacts_dir = Path(settings.ML_MODELS_DIR)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    rf_path = artifacts_dir / "lst_rf_model.joblib"
    xgb_path = artifacts_dir / "lst_xgb_model.json"
    
    joblib.dump(rf_model, rf_path)
    xgb_model.save_model(str(xgb_path))
    
    # Compute feature importances
    rf_importances = dict(zip(features, [round(float(v), 4) for v in rf_model.feature_importances_]))
    xgb_importances = dict(zip(features, [round(float(v), 4) for v in xgb_model.feature_importances_]))
    
    logger.info(
        "Models trained and evaluated successfully",
        rf_r2=round(rf_r2, 4),
        rf_mae=round(rf_mae, 4),
        xgb_r2=round(xgb_r2, 4),
        xgb_mae=round(xgb_mae, 4)
    )
    
    return {
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "features": features,
        "target": target,
        "rf": {
            "algorithm": "RandomForestRegressor",
            "artifact_path": str(rf_path),
            "mae": round(rf_mae, 3),
            "rmse": round(rf_rmse, 3),
            "r2": round(rf_r2, 3),
            "feature_importance": rf_importances
        },
        "xgb": {
            "algorithm": "XGBRegressor",
            "artifact_path": str(xgb_path),
            "mae": round(xgb_mae, 3),
            "rmse": round(xgb_rmse, 3),
            "r2": round(xgb_r2, 3),
            "feature_importance": xgb_importances
        }
    }
