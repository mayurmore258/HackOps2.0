"""
THERMOS AI - ThermoSim Intervention Simulation Service

Simulates potential environmental mitigation interventions:
- Urban Tree Canopy & Afforestation
- Cool Roof High-Albedo Retrofits
- Industrial-Residential Vegetative Green Buffers
- Low-Emission Traffic Corridor Management
- Combined Synergistic Interventions
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models.interventions import InterventionType, InterventionScenario, ScenarioComparison
from app.schemas.interventions import InterventionScenarioCreate

logger = get_logger(__name__)


class ThermoSimService:
    """Calculates assumption-based environmental scenario projections."""

    @classmethod
    def simulate_scenario(
        cls,
        intervention_code: str,
        area_sqm: float,
        parameters: Dict[str, float],
        baseline_lst: float = 38.5,
        baseline_nox: float = 145.0,
        baseline_risk: float = 72.0
    ) -> Dict[str, Any]:
        """
        Execute calibrated assumption-based simulation for an intervention scenario.
        Returns baseline indicators, simulated indicators, projected delta, and cost estimates.
        """
        code = intervention_code.lower()
        
        if code == "tree_planting":
            canopy_inc = float(parameters.get("tree_canopy_increase_pct", 30.0))
            # Scientific literature assumption: ~0.08 degC cooling per 1% canopy increase (Akbari et al.)
            temp_reduction = round(min(4.5, canopy_inc * 0.08), 2)
            # Particulate / NOx capture by dry deposition: ~0.25% per 1% canopy
            nox_reduction_pct = round(min(18.0, canopy_inc * 0.25), 1)
            # Tree cost ~ 1,200 INR per tree, 1 tree per 25 sqm
            tree_count = int(area_sqm / 25.0 * (canopy_inc / 100.0))
            cost_inr = tree_count * 1500.0
            assumptions = {
                "cooling_rate": "0.08 degC per 1% canopy expansion",
                "trees_planted_estimate": tree_count,
                "canopy_maturation_years": 4,
                "cost_per_sapling_maintenance_inr": 1500.0
            }

        elif code == "cool_roofs":
            albedo_inc = float(parameters.get("albedo_increase", 0.40))
            coverage_pct = float(parameters.get("roof_coverage_pct", 50.0))
            # Literature: ~0.06 degC regional surface cooling per 0.1 albedo increase at scale (Santamouris et al.)
            temp_reduction = round(min(4.0, (albedo_inc / 0.10) * 0.55 * (coverage_pct / 100.0)), 2)
            nox_reduction_pct = 0.0  # Cool roofs directly affect thermal radiation, not emissions
            roof_area_coated = area_sqm * (coverage_pct / 100.0)
            cost_inr = roof_area_coated * 28.0  # ~28 INR per sqm elastomeric coating
            assumptions = {
                "albedo_effect": "0.55 degC reduction per 0.1 albedo increase at 100% roof fraction",
                "roof_area_coated_sqm": roof_area_coated,
                "coating_lifespan_years": 5,
                "cost_per_sqm_inr": 28.0
            }

        elif code == "green_buffers":
            buffer_width_m = float(parameters.get("buffer_width_m", 100.0))
            density_pct = float(parameters.get("canopy_density_pct", 70.0))
            # Multi-tier vegetative screen
            temp_reduction = round(min(3.5, 1.2 + (buffer_width_m / 100.0) * 1.5 * (density_pct / 100.0)), 2)
            nox_reduction_pct = round(min(25.0, 8.0 + (buffer_width_m / 100.0) * 10.0), 1)
            cost_inr = area_sqm * 45.0  # ~45 INR per sqm site grading, tree planting, drip irrigation
            assumptions = {
                "particulate_filtration_rate": "Up to 25% dry deposition across 150m buffer",
                "width_meters": buffer_width_m,
                "cost_per_sqm_inr": 45.0
            }

        elif code == "traffic_management":
            freight_div_pct = float(parameters.get("freight_diversion_pct", 25.0))
            ev_share_pct = float(parameters.get("ev_bus_share_pct", 30.0))
            temp_reduction = 0.4  # Minor reduction in waste engine heat
            nox_reduction_pct = round(min(35.0, (freight_div_pct * 0.70) + (ev_share_pct * 0.40)), 1)
            cost_inr = 3500000.0  # Signage, intelligent transport system sensors, enforcement cameras
            assumptions = {
                "heavy_vehicle_emission_contribution": "Heavy diesel freight accounts for ~65% of corridor NOx",
                "ev_penetration_effect": "Direct zero tailpipe substitution",
                "capital_cost_inr": 3500000.0
            }

        elif code == "combined":
            # Synergistic multi-hazard mitigation
            temp_reduction = round(min(5.8, 2.5 + (area_sqm / 100000.0) * 0.5), 2)
            nox_reduction_pct = 24.5
            cost_inr = area_sqm * 38.0 + 4000000.0
            assumptions = {
                "synergy_multiplier": "Concurrent heat and emission reduction mitigates photochemical ozone formation",
                "integrated_coverage_sqm": area_sqm
            }
        else:
            raise ValidationError(f"Unknown intervention type: {intervention_code}")

        # Compute simulated outcomes
        simulated_lst = round(max(20.0, baseline_lst - temp_reduction), 2)
        simulated_nox = round(max(10.0, baseline_nox * (1.0 - (nox_reduction_pct / 100.0))), 2)
        
        # Risk score reduction is weighted composite of temperature reduction and emission reduction
        risk_reduction = round(min(30.0, (temp_reduction * 2.8) + (nox_reduction_pct * 0.45)), 1)
        simulated_risk = round(max(10.0, baseline_risk - risk_reduction), 1)

        return {
            "baseline_indicators": {
                "lst_celsius": baseline_lst,
                "nox_g_km_day": baseline_nox,
                "compound_risk_score": baseline_risk
            },
            "simulated_indicators": {
                "lst_celsius": simulated_lst,
                "nox_g_km_day": simulated_nox,
                "compound_risk_score": simulated_risk
            },
            "projected_temp_reduction_celsius": temp_reduction,
            "projected_emission_reduction_percent": nox_reduction_pct,
            "projected_risk_score_reduction": risk_reduction,
            "estimated_cost_inr": cost_inr,
            "assumptions": assumptions,
            "limitations": "Modelled assumption-based scenario simulation; not verified field microclimate measurements."
        }

    @staticmethod
    def list_intervention_types(db: Session) -> List[InterventionType]:
        """List all supported intervention categories."""
        return db.query(InterventionType).all()

    @staticmethod
    def list_scenarios(db: Session) -> List[InterventionScenario]:
        """List simulated scenarios."""
        return db.query(InterventionScenario).order_by(InterventionScenario.created_at.desc()).all()

    @staticmethod
    def get_scenario_by_id(db: Session, scenario_id: str) -> InterventionScenario:
        """Retrieve single scenario."""
        scen = db.query(InterventionScenario).filter(InterventionScenario.id == scenario_id).first()
        if not scen:
            raise ResourceNotFoundError("InterventionScenario", scenario_id)
        return scen

    @staticmethod
    def compare_scenarios(db: Session, scenario_ids: List[str]) -> Dict[str, Any]:
        """Compare 2 to 5 intervention scenarios side-by-side."""
        scenarios = db.query(InterventionScenario).filter(InterventionScenario.id.in_(scenario_ids)).all()
        if len(scenarios) < 2:
            raise ValidationError("At least two valid scenarios required for comparison.")

        table = []
        for s in scenarios:
            table.append({
                "scenario_name": s.name,
                "intervention_type": s.intervention_type.name if s.intervention_type else "Intervention",
                "area_sqm": s.simulated_area_sqm,
                "temp_reduction_celsius": s.projected_temp_reduction_celsius,
                "emission_reduction_pct": s.projected_emission_reduction_percent,
                "risk_reduction_points": s.projected_risk_score_reduction,
                "cost_inr": s.estimated_cost_inr,
                "cost_per_celsius_reduced_inr": round(s.estimated_cost_inr / max(0.1, s.projected_temp_reduction_celsius), 0)
            })

        # Determine best options
        best_cool = max(table, key=lambda x: x["temp_reduction_celsius"])
        best_emiss = max(table, key=lambda x: x["emission_reduction_pct"])
        best_cost = min(table, key=lambda x: x["cost_per_celsius_reduced_inr"])

        trade_off = (
            f"'{best_cool['scenario_name']}' delivers greatest surface cooling (-{best_cool['temp_reduction_celsius']} degC). "
            f"'{best_emiss['scenario_name']}' yields highest emission abatement (-{best_emiss['emission_reduction_pct']}% NOx). "
            f"'{best_cost['scenario_name']}' is most capital efficient ({best_cost['cost_per_celsius_reduced_inr']:,.0f} INR/degC)."
        )

        return {
            "scenarios": scenarios,
            "metrics_comparison_table": table,
            "most_cost_effective_option": best_cost["scenario_name"],
            "greatest_cooling_option": best_cool["scenario_name"],
            "greatest_emission_reduction_option": best_emiss["scenario_name"],
            "trade_off_analysis": trade_off,
            "disclaimer": "Simulated estimates are comparative decision-support projections, not guaranteed engineering measurements."
        }

