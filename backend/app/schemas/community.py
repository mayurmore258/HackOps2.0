"""
THERMOS AI - Community Exposure and Vulnerability Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SensitiveLocationItem(BaseModel):
    id: str
    name: str
    category: str  # hospital, school, elder_care, park, dense_residential
    latitude: float
    longitude: float
    address: Optional[str] = None
    capacity: Optional[int] = None
    distance_to_nearest_hotspot_m: Optional[float] = None


class AreaExposureItem(BaseModel):
    id: str
    area_name: str
    admin_level: str
    population: int
    area_sqkm: Optional[float] = None
    hazard_index: float = Field(..., ge=0.0, le=100.0)
    exposure_index: float = Field(..., ge=0.0, le=100.0)
    vulnerability_index: float = Field(..., ge=0.0, le=100.0)
    overall_risk_index: float = Field(..., ge=0.0, le=100.0)
    sensitive_facilities_count: int
    assessment_date: str
    limitations: str
    data_classification: str


class CommunitySummaryResponse(BaseModel):
    region_name: str
    total_population_screened: int
    population_in_high_risk_zones: int
    sensitive_locations_total: int
    sensitive_locations_in_hotspots: int
    mean_vulnerability_index: float
    most_exposed_area: str
    data_classification: str = "estimated"
    limitations: str = "Screening indicators based on spatial proximity; does not infer clinical diagnosis."

