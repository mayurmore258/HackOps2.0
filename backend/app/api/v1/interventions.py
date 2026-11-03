"""
THERMOS AI - ThermoSim Intervention Scenario Simulator API Router
"""

from typing import List
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.interventions.service import ThermoSimService
from app.schemas.common import ResponseEnvelope, ResponseMetadata
from app.schemas.interventions import (
    InterventionTypeResponse,
    InterventionScenarioCreate,
    InterventionScenarioResponse,
    ScenarioCompareRequest,
    ScenarioCompareResponse,
)
from app.db.models.interventions import InterventionType, InterventionScenario

router = APIRouter(prefix="/interventions", tags=["ThermoSim Intervention Simulator"])


@router.get("/types", response_model=ResponseEnvelope[List[InterventionTypeResponse]])
def list_intervention_types(db: Session = Depends(get_db)):
    """List supported urban heat and pollution mitigation intervention mechanisms."""
    types = ThermoSimService.list_intervention_types(db)
    items = [
        InterventionTypeResponse(
            id=str(t.id),
            code=t.code,
            name=t.name,
            description=t.description,
            category=t.category,
            default_parameters=t.default_parameters,
            scientific_rationale=t.scientific_rationale,
            known_limitations=t.known_limitations
        )
        for t in types
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="ThermoSim Scientific Mitigation Catalogue", classification="modelled")
    )


@router.get("/scenarios", response_model=ResponseEnvelope[List[InterventionScenarioResponse]])
def list_scenarios(db: Session = Depends(get_db)):
    """List previously evaluated intervention scenarios and their simulated outcomes."""
    scenarios = ThermoSimService.list_scenarios(db)
    items = [
        InterventionScenarioResponse(
            id=str(s.id),
            name=s.name,
            intervention_type=s.intervention_type.name if s.intervention_type else "Intervention",
            simulated_area_sqm=s.simulated_area_sqm,
            scenario_parameters=s.scenario_parameters,
            baseline_indicators=s.baseline_indicators,
            simulated_indicators=s.simulated_indicators,
            projected_temp_reduction_celsius=s.projected_temp_reduction_celsius,
            projected_emission_reduction_percent=s.projected_emission_reduction_percent,
            projected_risk_score_reduction=s.projected_risk_score_reduction,
            estimated_cost_inr=s.estimated_cost_inr,
            assumptions=s.assumptions_json,
            limitations=s.limitations,
            data_classification=s.data_classification,
            created_at=s.created_at.isoformat()
        )
        for s in scenarios
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="ThermoSim Scenario Database", classification="simulated")
    )


@router.get("/scenarios/{id}", response_model=ResponseEnvelope[InterventionScenarioResponse])
def get_scenario(
    id: str = Path(..., description="Scenario ID"),
    db: Session = Depends(get_db)
):
    """Retrieve full details, baseline indicators, and projected impacts for a specific scenario."""
    s = ThermoSimService.get_scenario_by_id(db, id)
    item = InterventionScenarioResponse(
        id=str(s.id),
        name=s.name,
        intervention_type=s.intervention_type.name if s.intervention_type else "Intervention",
        simulated_area_sqm=s.simulated_area_sqm,
        scenario_parameters=s.scenario_parameters,
        baseline_indicators=s.baseline_indicators,
        simulated_indicators=s.simulated_indicators,
        projected_temp_reduction_celsius=s.projected_temp_reduction_celsius,
        projected_emission_reduction_percent=s.projected_emission_reduction_percent,
        projected_risk_score_reduction=s.projected_risk_score_reduction,
        estimated_cost_inr=s.estimated_cost_inr,
        assumptions=s.assumptions_json,
        limitations=s.limitations,
        data_classification=s.data_classification,
        created_at=s.created_at.isoformat()
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="ThermoSim Scenario Detail", classification="simulated")
    )


@router.post("/scenarios", response_model=ResponseEnvelope[InterventionScenarioResponse])
def create_scenario(
    req: InterventionScenarioCreate,
    db: Session = Depends(get_db)
):
    """
    Simulate a new what-if environmental intervention scenario.
    Computes cooling impact, emission reduction, and cost estimations.
    """
    type_obj = db.query(InterventionType).filter(InterventionType.code == req.intervention_type_code.lower()).first()
    if not type_obj:
        # Fallback to first available
        type_obj = db.query(InterventionType).first()

    sim_result = ThermoSimService.simulate_scenario(
        intervention_code=req.intervention_type_code,
        area_sqm=req.area_sqm,
        parameters=req.parameters,
        baseline_lst=req.baseline_lst_celsius or 38.5,
        baseline_nox=req.baseline_nox_g_km_day or 145.0,
        baseline_risk=req.baseline_risk_score or 72.0
    )

    scenario = InterventionScenario(
        name=req.name,
        intervention_type_id=type_obj.id,
        region_id=None,
        simulated_area_sqm=req.area_sqm,
        scenario_parameters=req.parameters,
        baseline_indicators=sim_result["baseline_indicators"],
        simulated_indicators=sim_result["simulated_indicators"],
        projected_temp_reduction_celsius=sim_result["projected_temp_reduction_celsius"],
        projected_emission_reduction_percent=sim_result["projected_emission_reduction_percent"],
        projected_risk_score_reduction=sim_result["projected_risk_score_reduction"],
        estimated_cost_inr=sim_result["estimated_cost_inr"],
        assumptions_json=sim_result["assumptions"],
        limitations=sim_result["limitations"],
        data_classification="simulated"
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    item = InterventionScenarioResponse(
        id=str(scenario.id),
        name=scenario.name,
        intervention_type=type_obj.name,
        simulated_area_sqm=scenario.simulated_area_sqm,
        scenario_parameters=scenario.scenario_parameters,
        baseline_indicators=scenario.baseline_indicators,
        simulated_indicators=scenario.simulated_indicators,
        projected_temp_reduction_celsius=scenario.projected_temp_reduction_celsius,
        projected_emission_reduction_percent=scenario.projected_emission_reduction_percent,
        projected_risk_score_reduction=scenario.projected_risk_score_reduction,
        estimated_cost_inr=scenario.estimated_cost_inr,
        assumptions=scenario.assumptions_json,
        limitations=scenario.limitations,
        data_classification="simulated",
        created_at=scenario.created_at.isoformat()
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="ThermoSim What-If Engine", classification="simulated")
    )


@router.post("/compare", response_model=ResponseEnvelope[ScenarioCompareResponse])
def compare_scenarios(
    req: ScenarioCompareRequest,
    db: Session = Depends(get_db)
):
    """Compare multiple intervention scenarios side-by-side to assess trade-offs and cost effectiveness."""
    result = ThermoSimService.compare_scenarios(db, req.scenario_ids)
    
    scenario_items = [
        InterventionScenarioResponse(
            id=str(s.id),
            name=s.name,
            intervention_type=s.intervention_type.name if s.intervention_type else "Intervention",
            simulated_area_sqm=s.simulated_area_sqm,
            scenario_parameters=s.scenario_parameters,
            baseline_indicators=s.baseline_indicators,
            simulated_indicators=s.simulated_indicators,
            projected_temp_reduction_celsius=s.projected_temp_reduction_celsius,
            projected_emission_reduction_percent=s.projected_emission_reduction_percent,
            projected_risk_score_reduction=s.projected_risk_score_reduction,
            estimated_cost_inr=s.estimated_cost_inr,
            assumptions=s.assumptions_json,
            limitations=s.limitations,
            data_classification=s.data_classification,
            created_at=s.created_at.isoformat()
        )
        for s in result["scenarios"]
    ]

    return ResponseEnvelope(
        success=True,
        data=ScenarioCompareResponse(
            scenarios=scenario_items,
            metrics_comparison_table=result["metrics_comparison_table"],
            most_cost_effective_option=result["most_cost_effective_option"],
            greatest_cooling_option=result["greatest_cooling_option"],
            greatest_emission_reduction_option=result["greatest_emission_reduction_option"],
            trade_off_analysis=result["trade_off_analysis"],
            disclaimer=result["disclaimer"]
        ),
        metadata=ResponseMetadata(source="ThermoSim Decision Support Matrix", classification="simulated")
    )

