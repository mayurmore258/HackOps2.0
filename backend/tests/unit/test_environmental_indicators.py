"""
Unit tests for scientific environmental indicator calculations.
"""

import numpy as np
import pytest

from app.modules.heat.service import HeatIntelligenceService
from app.modules.risk.service import CompoundHotspotService
from app.modules.interventions.service import ThermoSimService
from app.schemas.hotspots import HotspotWeightsConfig


def test_ndvi_calculation():
    """Verify NDVI calculation: (NIR - Red) / (NIR + Red)."""
    nir = np.array([0.5, 0.4, 0.1])
    red = np.array([0.1, 0.2, 0.1])
    
    ndvi = HeatIntelligenceService.calculate_ndvi(nir, red)
    assert len(ndvi) == 3
    # First: (0.5 - 0.1) / (0.5 + 0.1) = 0.4 / 0.6 = 0.6667
    assert pytest.approx(ndvi[0], 0.001) == 0.6667
    # Second: (0.4 - 0.2) / (0.4 + 0.2) = 0.2 / 0.6 = 0.3333
    assert pytest.approx(ndvi[1], 0.001) == 0.3333
    # Third: (0.1 - 0.1) / (0.1 + 0.1) = 0.0
    assert pytest.approx(ndvi[2], 0.001) == 0.0


def test_ndbi_calculation():
    """Verify NDBI calculation: (SWIR - NIR) / (SWIR + NIR)."""
    swir = np.array([0.6, 0.2])
    nir = np.array([0.2, 0.6])
    
    ndbi = HeatIntelligenceService.calculate_ndbi(swir, nir)
    assert pytest.approx(ndbi[0], 0.001) == 0.50
    assert pytest.approx(ndbi[1], 0.001) == -0.50


def test_lst_from_brightness_temp():
    """Verify split-window / single channel emissivity corrected LST derivation."""
    bt_kelvin = 310.0  # ~36.85 degC brightness temperature
    fvc = 0.30  # 30% vegetation fraction
    lst_c = HeatIntelligenceService.calculate_lst_from_brightness_temp(bt_kelvin, fvc)
    
    # Should be close to 37 - 39 degC
    assert 35.0 <= lst_c <= 42.0


def test_compound_risk_calculation():
    """Verify ThermoSim composite risk score and severity classifications."""
    weights = HotspotWeightsConfig(heat_weight=0.30, industrial_weight=0.25, vehicular_weight=0.25, exposure_weight=0.20)
    
    # Critical scenario
    score, sev = CompoundHotspotService.calculate_compound_score(90.0, 85.0, 80.0, 80.0, weights)
    # 0.3*90 + 0.25*85 + 0.25*80 + 0.2*80 = 27 + 21.25 + 20 + 16 = 84.25
    assert score == 84.25
    assert sev == "critical"
    
    # Low scenario
    score_low, sev_low = CompoundHotspotService.calculate_compound_score(30.0, 20.0, 25.0, 20.0, weights)
    assert score_low < 45.0
    assert sev_low == "low"


def test_thermosim_scenario_simulation():
    """Verify ThermoSim intervention physics assumptions."""
    # Tree planting scenario
    sim = ThermoSimService.simulate_scenario(
        intervention_code="tree_planting",
        area_sqm=50000.0,
        parameters={"tree_canopy_increase_pct": 30.0},
        baseline_lst=40.0,
        baseline_nox=150.0,
        baseline_risk=75.0
    )
    assert sim["projected_temp_reduction_celsius"] > 1.5
    assert sim["simulated_indicators"]["lst_celsius"] < 40.0
    assert sim["simulated_indicators"]["compound_risk_score"] < 75.0
    assert sim["estimated_cost_inr"] > 0

