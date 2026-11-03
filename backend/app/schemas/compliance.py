"""
THERMOS AI - Environmental Compliance Screening Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StandardThresholdResponse(BaseModel):
    id: str
    parameter: str
    limit_value: float
    unit: str
    averaging_period: str
    area_category: str
    sampling_method: Optional[str] = None
    applicability_clause: Optional[str] = None


class EnvironmentalStandardResponse(BaseModel):
    id: str
    authority_name: str
    code: str
    title: str
    document_identifier: Optional[str] = None
    category: str
    source_url: Optional[str] = None
    summary: Optional[str] = None
    thresholds: List[StandardThresholdResponse] = Field(default_factory=list)


class ComplianceScreeningRequest(BaseModel):
    parameter: str = Field(..., description="e.g. PM10, PM2.5, SO2, NO2")
    observed_value: float = Field(..., description="Measured or observed value")
    unit: str = Field(..., description="Concentration unit (ug/m3, mg/m3, etc.)")
    averaging_period: str = Field(default="24h", description="Averaging period: 1h, 8h, 24h, annual")
    area_category: str = Field(default="residential_rural", description="residential_rural, industrial, sensitive")
    facility_id: Optional[str] = None
    monitoring_location_id: Optional[str] = None
    notes: Optional[str] = None


class ComplianceAssessmentResponse(BaseModel):
    id: str
    parameter: str
    observed_value: float
    unit: str
    averaging_period: str
    threshold_value: float
    ratio_to_threshold: float
    status: str  # within_reference_limit, potential_exceedance, insufficient_evidence, not_applicable, pending_review, human_review_required
    standard_title: str
    authority: str
    assessment_notes: str
    limitations: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_decision: Optional[str] = None


class ComplianceReviewRequest(BaseModel):
    reviewer_name: str = Field(..., description="Authorized environmental reviewer identity")
    decision: str = Field(..., description="confirmed_concern | false_alarm | further_investigation_required")
    review_notes: str = Field(..., description="Technical rationale for review decision")

