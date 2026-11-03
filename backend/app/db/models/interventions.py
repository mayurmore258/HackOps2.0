"""
THERMOS AI - ThermoSim Intervention Simulation Models
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.db.base import Base, UUIDMixin, TimestampMixin, SpatialGeometry


class InterventionType(Base, UUIDMixin, TimestampMixin):
    """Catalogue of environmental intervention types."""
    __tablename__ = "intervention_types"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), default="nature_based", nullable=False)  # nature_based, material, traffic, zoning
    default_parameters = Column(JSON, nullable=False)
    scientific_rationale = Column(Text, nullable=False)
    known_limitations = Column(Text, nullable=False)

    scenarios = relationship("InterventionScenario", back_populates="intervention_type")


class InterventionScenario(Base, UUIDMixin, TimestampMixin):
    """Specific simulation scenario run by an urban planner or environmental authority."""
    __tablename__ = "intervention_scenarios"

    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    intervention_type_id = Column(UUIDMixin.id.type, ForeignKey("intervention_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    region_id = Column(UUIDMixin.id.type, ForeignKey("regions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    target_geom = Column(SpatialGeometry("POLYGON", srid=4326), nullable=True)
    simulated_area_sqm = Column(Float, nullable=False)
    
    # Input parameters
    scenario_parameters = Column(JSON, nullable=False)  # e.g., tree_density, albedo_increase, traffic_reduction_pct
    
    # Baseline vs Simulated
    baseline_indicators = Column(JSON, nullable=False)  # baseline LST, NDVI, NOx, Risk Score
    simulated_indicators = Column(JSON, nullable=False)  # projected LST, projected NOx, projected Risk Score
    
    # Key Projected Impacts
    projected_temp_reduction_celsius = Column(Float, nullable=True)
    projected_emission_reduction_percent = Column(Float, nullable=True)
    projected_risk_score_reduction = Column(Float, nullable=True)
    estimated_cost_inr = Column(Float, nullable=True)
    
    # Provenance and Disclaimer
    assumptions_json = Column(JSON, nullable=False)
    limitations = Column(Text, default="Simulated scenario projection based on assumptions; not guaranteed physical microclimate measurement.", nullable=False)
    data_classification = Column(String(30), default="simulated", nullable=False)
    created_by = Column(String(100), default="environmental_analyst", nullable=False)

    intervention_type = relationship("InterventionType", back_populates="scenarios")


class ScenarioComparison(Base, UUIDMixin, TimestampMixin):
    """Side-by-side evaluation of two intervention options or baseline vs option."""
    __tablename__ = "scenario_comparisons"

    title = Column(String(150), nullable=False)
    scenario_a_id = Column(UUIDMixin.id.type, ForeignKey("intervention_scenarios.id", ondelete="CASCADE"), nullable=False)
    scenario_b_id = Column(UUIDMixin.id.type, ForeignKey("intervention_scenarios.id", ondelete="CASCADE"), nullable=False)
    comparison_metrics = Column(JSON, nullable=False)
    trade_off_notes = Column(Text, nullable=False)
    recommended_option = Column(String(50), nullable=True)

