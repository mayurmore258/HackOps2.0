"""
THERMOS AI - ThermoSim Intervention Simulator Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InterventionTypeResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    category: str
    default_parameters: Dict[str, Any]
    scientific_rationale: str
    known_limitations: str


class InterventionScenarioCreate(BaseModel):
    name: str = Field(..., description="Scenario descriptive name")
    intervention_type_code: str = Field(..., description="tree_planting, cool_roofs, green_buffers, traffic_management, combined")
    region_id: Optional[str] = None
    area_sqm: float = Field(..., gt=0.0, description="Area in square meters subject to intervention")
    parameters: Dict[str, float] = Field(
        ...,
        description="Scenario inputs (e.g., {'tree_canopy_increase_pct': 30.0, 'albedo_increase': 0.40, 'traffic_reduction_pct': 25.0})"
    )
    baseline_lst_celsius: Optional[float] = Field(default=38.5, description="Baseline LST in Celsius")
    baseline_nox_g_km_day: Optional[float] = Field(default=145.0, description="Baseline NOx emissions")
    baseline_risk_score: Optional[float] = Field(default=72.0, description="Baseline risk score (0-100)")


class InterventionScenarioResponse(BaseModel):
    id: str
    name: str
    intervention_type: str
    simulated_area_sqm: float
    scenario_parameters: Dict[str, Any]
    baseline_indicators: Dict[str, Any]
    simulated_indicators: Dict[str, Any]
    projected_temp_reduction_celsius: float
    projected_emission_reduction_percent: float
    projected_risk_score_reduction: float
    estimated_cost_inr: float
    assumptions: Dict[str, Any]
    limitations: str
    data_classification: str = "simulated"
    created_at: str


class ScenarioCompareRequest(BaseModel):
    scenario_ids: List[str] = Field(..., min_length=2, max_length=5, description="List of scenario IDs to compare")


class ScenarioCompareResponse(BaseModel):
    scenarios: List[InterventionScenarioResponse]
    metrics_comparison_table: List[Dict[str, Any]]
    most_cost_effective_option: str
    greatest_cooling_option: str
    greatest_emission_reduction_option: str
    trade_off_analysis: str
    disclaimer: str

