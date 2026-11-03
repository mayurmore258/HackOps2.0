"""
THERMOS AI - Regulatory Standards, Benchmarks, and Compliance Screening Models
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.db.base import Base, UUIDMixin, TimestampMixin


class RegulatoryAuthority(Base, UUIDMixin, TimestampMixin):
    """Statutory environmental regulatory bodies (CPCB, MPCB, MoEFCC)."""
    __tablename__ = "regulatory_authorities"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    country = Column(String(50), default="India", nullable=False)
    jurisdiction = Column(String(100), default="National / Maharashtra", nullable=False)
    website_url = Column(String(255), nullable=True)

    standards = relationship("EnvironmentalStandard", back_populates="authority")


class EnvironmentalStandard(Base, UUIDMixin, TimestampMixin):
    """Enacted standard document (e.g. National Ambient Air Quality Standards 2009)."""
    __tablename__ = "environmental_standards"

    authority_id = Column(UUIDMixin.id.type, ForeignKey("regulatory_authorities.id", ondelete="RESTRICT"), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    document_identifier = Column(String(100), nullable=True)  # e.g., G.S.R. 826(E)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    category = Column(String(50), default="ambient_air", nullable=False)  # ambient_air, industrial_stack, noise, water
    source_url = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    authority = relationship("RegulatoryAuthority", back_populates="standards")
    thresholds = relationship("StandardThreshold", back_populates="standard", cascade="all, delete-orphan")


class StandardThreshold(Base, UUIDMixin, TimestampMixin):
    """Exact machine-readable regulatory concentration/level threshold."""
    __tablename__ = "standard_thresholds"

    standard_id = Column(UUIDMixin.id.type, ForeignKey("environmental_standards.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter = Column(String(30), nullable=False, index=True)  # PM10, PM2.5, SO2, NO2, CO, Leq_Day
    limit_value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)  # ug/m3, mg/m3, dB(A)
    averaging_period = Column(String(30), nullable=False)  # 24h, annual, 8h, 1h, day, night
    area_category = Column(String(50), default="residential_rural", nullable=False)  # industrial, residential_rural, sensitive
    sampling_method = Column(String(100), nullable=True)
    applicability_clause = Column(Text, nullable=True)

    standard = relationship("EnvironmentalStandard", back_populates="thresholds")
    compliance_assessments = relationship("ComplianceAssessment", back_populates="standard_threshold")


class ComplianceAssessment(Base, UUIDMixin, TimestampMixin):
    """
    Automated and reviewed screening assessment comparing observed environmental
    indicators against compatible standards.
    """
    __tablename__ = "compliance_assessments"

    standard_threshold_id = Column(UUIDMixin.id.type, ForeignKey("standard_thresholds.id", ondelete="RESTRICT"), nullable=False, index=True)
    monitoring_location_id = Column(UUIDMixin.id.type, ForeignKey("monitoring_locations.id", ondelete="SET NULL"), nullable=True, index=True)
    facility_id = Column(UUIDMixin.id.type, ForeignKey("industrial_facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    
    parameter = Column(String(30), nullable=False)
    observed_value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    averaging_period = Column(String(30), nullable=False)
    threshold_value = Column(Float, nullable=False)
    ratio_to_threshold = Column(Float, nullable=False)  # observed / threshold
    
    # Strictly screening states, not legal determinations
    # within_reference_limit, potential_exceedance, insufficient_evidence, not_applicable, pending_review, human_review_required
    status = Column(String(40), default="potential_exceedance", nullable=False, index=True)
    
    assessment_notes = Column(Text, nullable=False)
    limitations = Column(Text, default="Preliminary technical screening; official legal determination requires certified statutory sampling and formal review.", nullable=False)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_decision = Column(String(50), nullable=True)  # confirmed_concern, false_alarm, further_investigation_required

    standard_threshold = relationship("StandardThreshold", back_populates="compliance_assessments")
    facility = relationship("IndustrialFacility", back_populates="compliance_assessments")
    evidence = relationship("ComplianceEvidence", back_populates="compliance_assessment", cascade="all, delete-orphan")


class ComplianceEvidence(Base, UUIDMixin, TimestampMixin):
    """Audit evidence attached to a compliance assessment."""
    __tablename__ = "compliance_evidence"

    compliance_assessment_id = Column(UUIDMixin.id.type, ForeignKey("compliance_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type = Column(String(50), nullable=False)  # monitoring_data, satellite_scene, inspection_report, permit_clause
    file_uri = Column(String(255), nullable=True)
    checksum = Column(String(64), nullable=True)
    notes = Column(Text, nullable=False)
    provenance_metadata = Column(JSON, nullable=True)

    compliance_assessment = relationship("ComplianceAssessment", back_populates="evidence")

