"""
THERMOS AI - Environmental Hotspot and Compound Risk Intelligence Models
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.db.base import Base, UUIDMixin, TimestampMixin, SpatialGeometry


class HeatHotspot(Base, UUIDMixin, TimestampMixin):
    """Identified local urban heat island / elevated thermal anomaly."""
    __tablename__ = "heat_hotspots"

    region_id = Column(UUIDMixin.id.type, ForeignKey("regions.id", ondelete="CASCADE"), nullable=False, index=True)
    hotspot_code = Column(String(50), nullable=True, index=True)
    severity = Column(String(20), default="moderate", nullable=False)  # low, moderate, high, extreme
    lst_celsius = Column(Float, nullable=False)
    lst_anomaly_celsius = Column(Float, nullable=False)  # Elevation above regional background mean
    ndvi = Column(Float, nullable=True)
    ndbi = Column(Float, nullable=True)
    area_sqkm = Column(Float, nullable=True)
    geom = Column(SpatialGeometry("POLYGON", srid=4326), nullable=True)
    detected_date = Column(DateTime(timezone=True), nullable=False, index=True)
    contributing_factors = Column(JSON, nullable=True)
    data_classification = Column(String(30), default="satellite_derived", nullable=False)

    region = relationship("Region", back_populates="heat_hotspots")


class IndustrialHotspot(Base, UUIDMixin, TimestampMixin):
    """Potential industrial emission indicator hotspot (TROPOMI atmospheric column or ground cluster)."""
    __tablename__ = "industrial_hotspots"

    facility_id = Column(UUIDMixin.id.type, ForeignKey("industrial_facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    hotspot_code = Column(String(50), nullable=True, index=True)
    pollutant = Column(String(20), nullable=False)  # SO2, NO2
    concentration_estimate = Column(Float, nullable=False)
    unit = Column(String(30), default="mol/m2", nullable=False)
    severity = Column(String(20), default="moderate", nullable=False)
    wind_aligned = Column(Boolean, default=False, nullable=False)
    wind_direction_deg = Column(Float, nullable=True)
    geom = Column(SpatialGeometry("POLYGON", srid=4326), nullable=True)
    detected_date = Column(DateTime(timezone=True), nullable=False, index=True)
    evidence_notes = Column(Text, nullable=True)
    data_classification = Column(String(30), default="satellite_derived", nullable=False)
    limitations = Column(Text, default="Atmospheric column indicator; does not establish verified legal emission violation of an individual stack.", nullable=False)

    facility = relationship("IndustrialFacility", back_populates="industrial_hotspots")


class VehicularHotspot(Base, UUIDMixin, TimestampMixin):
    """High-emission transport corridor or junction hotspot."""
    __tablename__ = "vehicular_hotspots"

    road_segment_id = Column(UUIDMixin.id.type, ForeignKey("road_segments.id", ondelete="SET NULL"), nullable=True, index=True)
    hotspot_code = Column(String(50), nullable=True, index=True)
    pollutant = Column(String(20), default="NOx", nullable=False)
    emission_intensity = Column(Float, nullable=False)  # e.g., g/km/day
    unit = Column(String(30), default="g/km/day", nullable=False)
    severity = Column(String(20), default="moderate", nullable=False)
    geom = Column(SpatialGeometry("MULTILINESTRING", srid=4326), nullable=True)
    detected_date = Column(DateTime(timezone=True), nullable=False, index=True)
    traffic_context = Column(Text, nullable=True)
    data_classification = Column(String(30), default="modelled", nullable=False)

    road_segment = relationship("RoadSegment", back_populates="vehicular_hotspots")


class CompoundHotspot(Base, UUIDMixin, TimestampMixin):
    """
    Signature ThermoSim Hotspot: Multi-hazard overlap where Urban Heat,
    Industrial Indicators, Vehicular Emissions, and Population Exposure intersect.
    """
    __tablename__ = "compound_hotspots"

    region_id = Column(UUIDMixin.id.type, ForeignKey("regions.id", ondelete="CASCADE"), nullable=False, index=True)
    hotspot_code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(150), nullable=False)
    
    # Normalized component scores (0 - 100)
    heat_score = Column(Float, nullable=False)
    industrial_score = Column(Float, nullable=False)
    vehicular_score = Column(Float, nullable=False)
    exposure_score = Column(Float, nullable=False)
    compound_risk_score = Column(Float, nullable=False, index=True)  # Overall weighted composite
    
    severity = Column(String(20), default="moderate", nullable=False, index=True)  # low, moderate, high, critical
    primary_hazard = Column(String(50), nullable=False)  # heat, industrial, vehicular, compound
    area_sqkm = Column(Float, nullable=True)
    geom = Column(SpatialGeometry("POLYGON", srid=4326), nullable=True)
    detected_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Explainability & Provenance
    contributing_evidence = Column(JSON, nullable=False)  # Breakdown of input data, metrics, and weights
    methodology_version = Column(String(50), default="ThermoSim-Composite-v1.0", nullable=False)
    limitations = Column(Text, nullable=False)
    data_classification = Column(String(30), default="modelled", nullable=False)

    region = relationship("Region", back_populates="compound_hotspots")
    exposure_assessments = relationship("CommunityExposureAssessment", back_populates="compound_hotspot")


class CommunityExposureAssessment(Base, UUIDMixin, TimestampMixin):
    """Community-level exposure, sensitive receptor analysis, and environmental screening."""
    __tablename__ = "community_exposure_assessments"

    administrative_area_id = Column(UUIDMixin.id.type, ForeignKey("administrative_areas.id", ondelete="CASCADE"), nullable=False, index=True)
    compound_hotspot_id = Column(UUIDMixin.id.type, ForeignKey("compound_hotspots.id", ondelete="SET NULL"), nullable=True, index=True)
    
    exposed_population = Column(Integer, nullable=False)
    sensitive_facilities_count = Column(Integer, default=0, nullable=False)
    
    # Screening Indices (0 - 100)
    hazard_index = Column(Float, nullable=False)
    exposure_index = Column(Float, nullable=False)
    vulnerability_index = Column(Float, nullable=False)
    overall_risk_index = Column(Float, nullable=False, index=True)
    
    assessment_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    breakdown_json = Column(JSON, nullable=True)
    limitations = Column(Text, default="Spatial screening index for prioritization; does not diagnose clinical health outcomes.", nullable=False)
    data_classification = Column(String(30), default="estimated", nullable=False)

    administrative_area = relationship("AdministrativeArea", back_populates="exposure_assessments")
    compound_hotspot = relationship("CompoundHotspot", back_populates="exposure_assessments")


class RiskAssessment(Base, UUIDMixin, TimestampMixin):
    """Targeted screening risk assessment report."""
    __tablename__ = "risk_assessments"

    title = Column(String(200), nullable=False)
    target_type = Column(String(50), nullable=False)  # region, ward, facility, corridor
    target_id = Column(String(100), nullable=True)
    overall_score = Column(Float, nullable=False)
    heat_component = Column(Float, nullable=False)
    air_component = Column(Float, nullable=False)
    exposure_component = Column(Float, nullable=False)
    rationale = Column(Text, nullable=False)
    recommended_focus = Column(Text, nullable=True)
    data_classification = Column(String(30), default="estimated", nullable=False)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

