"""
API Endpoint Integration Tests - THERMOS AI

Validates all primary API endpoints and workflows against the database session.
"""

import pytest
from app.db.session import SessionLocal
from app.main import root_health, api_v1_health
from app.api.v1.dashboard import get_dashboard_summary
from app.api.v1.heat import get_heat_summary, list_heat_hotspots, get_heat_geojson_layers
from app.api.v1.industrial import get_industrial_summary, list_industrial_facilities
from app.api.v1.vehicular import get_vehicular_summary, list_road_segments
from app.api.v1.hotspots import get_compound_hotspots_summary, list_compound_hotspots
from app.api.v1.interventions import (
    list_intervention_types,
    create_scenario,
    list_scenarios,
    compare_scenarios,
)
from app.api.v1.compliance import list_standards, screen_observation
from app.api.v1.incidents import (
    create_incident,
    analyse_incident,
    add_corrective_action,
    resolve_incident,
)
from app.api.v1.predictions import list_models, run_prediction

from app.schemas.interventions import InterventionScenarioCreate, ScenarioCompareRequest
from app.schemas.compliance import ComplianceScreeningRequest
from app.schemas.incidents import IncidentCreate, IncidentAnalyseRequest, CorrectiveActionCreate
from app.schemas.predictions import PredictionRunRequest


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_health_endpoints():
    """Verify system health check endpoints."""
    res = root_health()
    assert res["status"] == "healthy"
    assert "THERMOS AI" in res["app"]

    res_v1 = api_v1_health()
    assert res_v1["status"] in ("healthy", "degraded")
    assert res_v1["database"] == "connected"


def test_dashboard_summary(db):
    """Verify /api/v1/dashboard/summary response schema and data integrity."""
    envelope = get_dashboard_summary(db=db)
    assert envelope.success is True
    data = envelope.data
    assert data.hotspot_counts.compound_hotspots >= 1
    assert len(data.high_risk_locations) >= 1
    assert "Panvel" in data.pilot_region


def test_heat_endpoints(db):
    """Verify Urban Heat endpoints."""
    summary_env = get_heat_summary(region_code="PANVEL_NAVI_MUMBAI", db=db)
    assert summary_env.success is True
    assert summary_env.data.mean_lst_celsius > 0

    hotspots_env = list_heat_hotspots(db=db)
    assert hotspots_env.success is True
    assert isinstance(hotspots_env.data, list)
    assert len(hotspots_env.data) >= 1

    layers_env = get_heat_geojson_layers(db=db)
    assert layers_env.success is True
    assert layers_env.data.type == "FeatureCollection"
    assert len(layers_env.data.features) >= 1


def test_industrial_endpoints(db):
    """Verify Industrial Pollution endpoints."""
    summary_env = get_industrial_summary(region_code="PANVEL_NAVI_MUMBAI", db=db)
    assert summary_env.success is True
    assert summary_env.data.monitored_facilities_count >= 1

    fac_env = list_industrial_facilities(db=db)
    assert fac_env.success is True
    assert len(fac_env.data) >= 1


def test_vehicular_endpoints(db):
    """Verify Vehicular Emission endpoints."""
    summary_env = get_vehicular_summary(region_code="PANVEL_NAVI_MUMBAI", db=db)
    assert summary_env.success is True
    assert "CHETNA-Road" in summary_env.data.dataset_source

    roads_env = list_road_segments(db=db)
    assert roads_env.success is True
    assert len(roads_env.data) >= 1


def test_compound_hotspots_endpoints(db):
    """Verify Compound Hotspot multi-hazard intelligence endpoints."""
    summary_env = get_compound_hotspots_summary(region_code="PANVEL_NAVI_MUMBAI", db=db)
    assert summary_env.success is True
    assert summary_env.data.total_compound_hotspots >= 1

    comp_env = list_compound_hotspots(db=db)
    assert comp_env.success is True
    hotspots = comp_env.data
    assert len(hotspots) >= 1
    first = hotspots[0]
    assert first.heat_score > 0
    assert first.industrial_score > 0
    assert first.vehicular_score > 0
    assert first.exposure_score > 0
    assert first.compound_risk_score > 0


def test_interventions_simulation_and_comparison(db):
    """Verify ThermoSim What-If simulation and comparison endpoints."""
    types_env = list_intervention_types(db=db)
    assert types_env.success is True
    assert len(types_env.data) >= 3

    scen_payload = InterventionScenarioCreate(
        name="Kamothe Sector 36 Tree Canopy Retrofit",
        intervention_type_code="tree_planting",
        area_sqm=45000.0,
        parameters={"tree_canopy_increase_pct": 35.0},
        baseline_lst_celsius=41.5,
        baseline_nox_g_km_day=160.0,
        baseline_risk_score=78.0
    )
    create_env = create_scenario(req=scen_payload, db=db)
    assert create_env.success is True
    created = create_env.data
    assert created.projected_temp_reduction_celsius > 0
    scen_id_1 = created.id

    list_env = list_scenarios(db=db)
    assert list_env.success is True
    all_scens = list_env.data
    assert len(all_scens) >= 2
    scen_id_2 = all_scens[0].id if all_scens[0].id != scen_id_1 else all_scens[1].id

    cmp_payload = ScenarioCompareRequest(scenario_ids=[scen_id_1, scen_id_2])
    cmp_env = compare_scenarios(req=cmp_payload, db=db)
    assert cmp_env.success is True
    cmp_data = cmp_env.data
    assert cmp_data.trade_off_analysis is not None
    assert len(cmp_data.metrics_comparison_table) == 2


def test_compliance_screening_and_standards(db):
    """Verify Statutory Standards and Screening Assessments."""
    stds_env = list_standards(db=db)
    assert stds_env.success is True
    assert len(stds_env.data) >= 1

    screen_req = ComplianceScreeningRequest(
        parameter="PM10",
        observed_value=142.0,
        unit="ug/m3",
        averaging_period="24h",
        area_category="residential_rural"
    )
    ass_env = screen_observation(req=screen_req, db=db)
    assert ass_env.success is True
    ass = ass_env.data
    assert ass.status == "potential_exceedance"
    assert ass.ratio_to_threshold > 1.0


def test_incident_reporting_workflow(db):
    """Verify Incident creation -> analysis -> corrective action assignment -> resolution."""
    inc_payload = IncidentCreate(
        title="Dense smoke and particulate fallout near Kharghar Station",
        description="Thick black particulate fallout covering parked vehicles; citizen complaint.",
        category="air_pollution",
        severity="medium",
        latitude=19.0435,
        longitude=73.0682,
        address="Kharghar Station Road",
        reporter_name="Arun Shinde",
        reporter_type="citizen"
    )
    create_env = create_incident(req=inc_payload, db=db)
    assert create_env.success is True
    inc = create_env.data
    inc_id = inc.id
    assert inc.incident_number.startswith("INC-2026-")
    assert inc.status == "reported"

    analyse_req = IncidentAnalyseRequest(buffer_radius_meters=3000.0)
    analyse_env = analyse_incident(id=inc_id, req=analyse_req, db=db)
    assert analyse_env.success is True
    assert len(analyse_env.data.nearby_heat_hotspots) >= 1 or len(analyse_env.data.nearby_vehicular_corridors) >= 1
    assert analyse_env.data.nearest_compound_hotspot is not None

    action_payload = CorrectiveActionCreate(
        title="Deploy mobile mist cannon for dust suppression",
        description="Deploy PMC water mist cannon to suppress construction dust along road corridor.",
        action_type="dust_suppression",
        priority="high",
        assigned_to="PMC Rapid Response Team",
        assigned_department="Public Health & Sanitation, PMC"
    )
    action_env = add_corrective_action(id=inc_id, req=action_payload, db=db)
    assert action_env.success is True
    action = action_env.data
    assert action.status == "assigned"

    resolve_env = resolve_incident(id=inc_id, db=db)
    assert resolve_env.success is True
    assert resolve_env.data.status == "resolved"


def test_predictions_api(db):
    """Verify AI/ML inference endpoint."""
    models_env = list_models(db=db)
    assert models_env.success is True
    assert len(models_env.data) >= 1

    run_payload = PredictionRunRequest(
        target_variable="lst_celsius",
        horizon="next_period",
        input_features={
            "ndvi": 0.20,
            "ndbi": 0.35,
            "solar_radiation": 820.0,
            "day_of_year": 130.0
        },
        algorithm="RandomForest"
    )
    pred_env = run_prediction(req=run_payload, db=db)
    assert pred_env.success is True
    pred = pred_env.data
    assert pred.predicted_value > 25.0
    assert pred.explanation is not None
    assert "top_contributing_features" in pred.explanation or isinstance(pred.explanation, dict)
