"""
THERMOS AI — Comprehensive Unseen Data Validation & Generalization Test Suite

Validates that the entire product functions reliably on completely unseen environmental data:
1. AI/ML Model Generalization on out-of-distribution / unseen microclimatic extremes.
2. Ingestion pipelines on unseen CSV sensor streams and GeoJSON boundaries.
3. GIS spatial metric engine on unseen coordinates (Thane-Belapur / TTC).
4. Environmental intelligence calculations on unseen thermal and emission values.
5. ThermoSim What-If Intervention simulator on unseen scenario parameters.
6. Statutory compliance screening on unseen extreme observations.
7. End-to-end incident lifecycle on an unseen geographic incident.
"""

import json
import math
import tempfile
from pathlib import Path
import pytest
import numpy as np

from app.db.session import SessionLocal
from app.db.spatial import (
    point_from_coordinates,
    haversine_distance_km,
    calculate_area_sqm,
    buffer_point_meters,
    point_in_polygon,
    geometry_to_geojson_dict,
)
from app.data_pipeline.ingestion.csv_pipeline import CSVIngestionPipeline
from app.data_pipeline.ingestion.geojson_pipeline import GeoJSONIngestionPipeline
from app.modules.heat.service import HeatIntelligenceService
from app.modules.industrial.service import IndustrialIntelligenceService
from app.modules.vehicular.service import VehicularIntelligenceService
from app.modules.risk.service import CompoundHotspotService
from app.modules.interventions.service import ThermoSimService
from app.modules.compliance.service import ComplianceScreeningService
from app.modules.incidents.service import IncidentService
from ml.inference.predictor import LSTPredictor

from app.schemas.hotspots import HotspotWeightsConfig
from app.schemas.compliance import ComplianceScreeningRequest
from app.schemas.incidents import IncidentCreate, CorrectiveActionCreate, IncidentUpdate


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# -----------------------------------------------------------------------------
# 1. AI/ML Generalization on Unseen Microclimates & Edge Cases
# -----------------------------------------------------------------------------

def test_ml_generalization_on_unseen_extremes():
    """
    Test Random Forest and XGBoost predictors on 5 completely unseen microclimate scenarios:
    - Extreme Heatwave Core (High built density, peak summer solar radiation)
    - Dense Wetland / Mangrove Buffer (Negative NDBI, high NDVI)
    - Cool Winter Morning
    - High-Albedo Industrial Warehouse Zone
    - Mixed Urban Fringe
    """
    unseen_scenarios = [
        {
            "name": "Extreme Heatwave Core",
            "features": {"ndvi": 0.08, "ndbi": 0.58, "solar_radiation": 940.0, "day_of_year": 142.0},
            "expected_min_temp": 36.0,
        },
        {
            "name": "Dense Wetland Buffer",
            "features": {"ndvi": 0.72, "ndbi": -0.25, "solar_radiation": 750.0, "day_of_year": 210.0},
            "expected_max_temp": 34.0,
        },
        {
            "name": "Cool Winter Morning",
            "features": {"ndvi": 0.35, "ndbi": 0.15, "solar_radiation": 520.0, "day_of_year": 20.0},
            "expected_max_temp": 31.0,
        },
        {
            "name": "High-Albedo Industrial Roof Zone",
            "features": {"ndvi": 0.12, "ndbi": 0.28, "solar_radiation": 880.0, "day_of_year": 120.0},
            "expected_min_temp": 33.0,
        },
        {
            "name": "Mixed Urban Fringe",
            "features": {"ndvi": 0.40, "ndbi": 0.20, "solar_radiation": 780.0, "day_of_year": 95.0},
            "expected_min_temp": 30.0,
        },
    ]

    for sc in unseen_scenarios:
        # Test Random Forest
        rf_res = LSTPredictor.predict(sc["features"], algorithm="RandomForest")
        assert "predicted_value" in rf_res
        assert 20.0 <= rf_res["predicted_value"] <= 55.0, f"Unphysical RF temp for {sc['name']}"
        assert rf_res["lower_bound"] < rf_res["predicted_value"] < rf_res["upper_bound"]
        assert "explanation" in rf_res

        # Test XGBoost
        xgb_res = LSTPredictor.predict(sc["features"], algorithm="XGBoost")
        assert "predicted_value" in xgb_res
        assert 20.0 <= xgb_res["predicted_value"] <= 55.0, f"Unphysical XGB temp for {sc['name']}"

        # Verify physical sensitivity: Heatwave must be hotter than Wetland
        if sc["name"] == "Extreme Heatwave Core":
            assert rf_res["predicted_value"] >= sc["expected_min_temp"]
        elif sc["name"] == "Dense Wetland Buffer":
            assert rf_res["predicted_value"] <= sc["expected_max_temp"]


# -----------------------------------------------------------------------------
# 2. Ingestion Pipelines on Unseen Raw Streams
# -----------------------------------------------------------------------------

def test_ingestion_pipeline_on_unseen_csv():
    """Verify CSVIngestionPipeline parses and standardizes unseen tabular sensor logs."""
    pipeline = CSVIngestionPipeline(dataset_code="CAAQMS_MAHAPE_UNSEEN", source_code="CPCB_PORTAL")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("timestamp,pollutant,value,unit,station\n")
        f.write("2026-05-18T10:00:00Z,PM2.5,68.4,ug/m3,MAHAPE-01\n")
        f.write("2026-05-18T10:00:00Z,PM10,142.1,ug/m3,MAHAPE-01\n")
        f.write("2026-05-18T10:00:00Z,NO2,54.2,ug/m3,MAHAPE-01\n")
        temp_path = Path(f.name)

    try:
        assert pipeline.validate_file(temp_path) is True
        records = pipeline.parse_and_transform(temp_path)
        assert len(records) == 3
        assert records[0]["pollutant"] == "PM2.5"
        assert records[0]["value"] == 68.4
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_ingestion_pipeline_on_unseen_geojson():
    """Verify GeoJSONIngestionPipeline processes unseen administrative boundary polygons."""
    pipeline = GeoJSONIngestionPipeline(dataset_code="WARD_TTC_UNSEEN", source_code="MUNICIPAL_GIS")
    
    unseen_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"ward_name": "TTC Industrial Zone A", "zone_code": "TTC-01", "population": 42000},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[73.01, 19.12], [73.04, 19.12], [73.04, 19.15], [73.01, 19.15], [73.01, 19.12]]]
                }
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as f:
        json.dump(unseen_geojson, f)
        temp_path = Path(f.name)

    try:
        assert pipeline.validate_file(temp_path) is True
        features = pipeline.parse_and_transform(temp_path)
        assert len(features) == 1
        assert features[0]["properties"]["zone_code"] == "TTC-01"
    finally:
        if temp_path.exists():
            temp_path.unlink()


# -----------------------------------------------------------------------------
# 3. GIS Metric Engine on Unseen Coordinates
# -----------------------------------------------------------------------------

def test_gis_metric_engine_on_unseen_coordinates():
    """Verify UTM Zone 43N metric conversions on coordinates in Thane-Belapur corridor."""
    dist_km = haversine_distance_km(73.0080, 19.1350, 73.0150, 19.1480)
    assert 1.2 <= dist_km <= 2.0, f"Calculated distance {dist_km} km is out of expected physical bounds"

    poly_geojson = {
        "type": "Polygon",
        "coordinates": [
            [
                [73.00, 19.12],
                [73.03, 19.12],
                [73.03, 19.15],
                [73.00, 19.15],
                [73.00, 19.12],
            ]
        ]
    }
    area_sqm = calculate_area_sqm(poly_geojson)
    area_sqkm = area_sqm / 1e6
    assert 9.0 < area_sqkm < 12.0, f"Calculated area {area_sqkm} sq km is out of physical bounds"

    assert point_in_polygon(73.015, 19.135, poly_geojson) is True
    assert point_in_polygon(73.100, 19.200, poly_geojson) is False


# -----------------------------------------------------------------------------
# 4. Environmental Intelligence Calculations on Unseen Data
# -----------------------------------------------------------------------------

def test_environmental_intelligence_on_unseen_inputs():
    """Verify scientific calculations handle unseen thermal, spectral, and compound hazard inputs."""
    # Biophysical calculations on unseen spectral vectors
    nir = np.array([0.55, 0.45, 0.12])
    red = np.array([0.08, 0.22, 0.11])
    ndvi = HeatIntelligenceService.calculate_ndvi(nir, red)
    assert len(ndvi) == 3
    assert ndvi[0] > 0.70  # Dense vegetation

    # Thermal derivation
    lst = HeatIntelligenceService.calculate_lst_from_brightness_temp(315.0, 0.15)
    assert 38.0 <= lst <= 46.0

    # Compound Multi-Hazard Synthesis
    weights_cfg = HotspotWeightsConfig(heat_weight=0.30, industrial_weight=0.30, vehicular_weight=0.25, exposure_weight=0.15)
    compound_score, severity = CompoundHotspotService.calculate_compound_score(
        heat_score=85.0,
        industrial_score=92.0,
        vehicular_score=78.0,
        exposure_score=64.0,
        weights=weights_cfg
    )
    expected = 85.0 * 0.30 + 92.0 * 0.30 + 78.0 * 0.25 + 64.0 * 0.15
    assert math.isclose(compound_score, expected, rel_tol=1e-3)
    assert compound_score > 80.0
    assert severity in ("critical", "high")


# -----------------------------------------------------------------------------
# 5. ThermoSim Scenario Simulator on Unseen Interventions
# -----------------------------------------------------------------------------

def test_thermosim_simulation_on_unseen_scenario():
    """Verify ThermoSim What-If simulator on an unseen large industrial cool-roof scenario."""
    sim_res = ThermoSimService.simulate_scenario(
        intervention_code="cool_roofs",
        area_sqm=120000.0,
        parameters={"albedo_increase": 0.35},
        baseline_lst=43.5,
        baseline_nox=195.0,
        baseline_risk=86.0
    )
    assert sim_res["projected_temp_reduction_celsius"] > 0.5
    assert sim_res["estimated_cost_inr"] > 0
    assert sim_res["projected_risk_score_reduction"] > 0
    assert sim_res["simulated_indicators"]["compound_risk_score"] < 86.0


# -----------------------------------------------------------------------------
# 6. Statutory Compliance Screening on Unseen Extreme Observations
# -----------------------------------------------------------------------------

def test_compliance_screening_on_unseen_extreme_observations(db):
    """Verify statutory evaluation across unseen severe exceedances and clean observations."""
    # 1. Severe particulate exceedance (Dust storm / construction plume)
    screen_exceed = ComplianceScreeningRequest(
        parameter="PM10",
        observed_value=345.0,
        unit="ug/m3",
        averaging_period="24h",
        area_category="residential_rural"
    )
    res_exceed = ComplianceScreeningService.screen_observation(db, screen_exceed)
    assert res_exceed.status == "potential_exceedance"
    assert res_exceed.ratio_to_threshold > 3.0

    # 2. Compliant clean observation
    screen_compliant = ComplianceScreeningRequest(
        parameter="NO2",
        observed_value=28.0,
        unit="ug/m3",
        averaging_period="24h",
        area_category="residential_rural"
    )
    res_compliant = ComplianceScreeningService.screen_observation(db, screen_compliant)
    assert res_compliant.status == "within_reference_limit"
    assert res_compliant.ratio_to_threshold < 0.5


# -----------------------------------------------------------------------------
# 7. Incident Management Lifecycle on Unseen Geographic Coordinate
# -----------------------------------------------------------------------------

def test_incident_lifecycle_on_unseen_location(db):
    """
    Verify complete incident reporting and spatial context analysis
    on an unseen coordinate in Rabale, Navi Mumbai.
    """
    # 1. Log unseen incident
    new_inc = IncidentCreate(
        title="Unseen chemical plume and burning eye irritation in Rabale MIDC",
        description="Pungent sulphur-like smell reported by commuters exiting Rabale Station.",
        category="industrial_emission",
        severity="high",
        latitude=19.1350,
        longitude=73.0080,
        address="Near Rabale Railway Station, TTC Industrial Area",
        reporter_name="Sunil Patil",
        reporter_type="citizen"
    )
    created = IncidentService.create_incident(db, new_inc)
    assert created.incident_number.startswith("INC-2026-")
    assert created.status == "reported"

    # 2. Synthesize multi-hazard spatial context (5km buffer)
    analysis = IncidentService.analyse_incident_context(db, str(created.id), buffer_radius_m=5000.0)
    assert "applicable_standards" in analysis
    assert len(analysis["applicable_standards"]) >= 1
    assert "causation_disclaimer" in analysis

    # 3. Add corrective action
    action_req = CorrectiveActionCreate(
        title="Immediate MPCB Joint Site Inspection",
        description="Inspect chemical manufacturing units in Sector 8 Rabale.",
        action_type="site_inspection",
        priority="high",
        assigned_to="MPCB TTC Sub-Regional Office",
        assigned_department="Enforcement Wing, MPCB"
    )
    action = IncidentService.add_corrective_action(db, str(created.id), action_req)
    assert action.status == "assigned"

    # 4. Resolve incident
    resolved = IncidentService.update_incident(
        db,
        str(created.id),
        IncidentUpdate(status="resolved", resolution_notes="Completed site inspection.")
    )
    assert resolved.status == "resolved"
