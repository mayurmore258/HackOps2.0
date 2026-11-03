"""
THERMOS AI - Industrial Pollution Intelligence Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IndustrialSummaryResponse(BaseModel):
    region_name: str
    monitored_facilities_count: int
    red_category_facilities_count: int
    orange_category_facilities_count: int
    active_hotspots_count: int
    primary_pollutant_indicators: List[str]
    mean_so2_column_mol_m2: Optional[float] = None
    mean_no2_column_mol_m2: Optional[float] = None
    wind_condition_summary: Optional[str] = None
    data_classification: str
    limitations: str


class IndustrialFacilityResponse(BaseModel):
    id: str
    name: str
    industry_type: str
    category: str  # Red, Orange, Green
    consent_id: Optional[str] = None
    district: str
    state: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    is_cems_connected: bool


class IndustrialHotspotItem(BaseModel):
    id: str
    hotspot_code: Optional[str] = None
    facility_name: Optional[str] = None
    facility_id: Optional[str] = None
    pollutant: str
    concentration_estimate: float
    unit: str
    severity: str
    wind_aligned: bool
    wind_direction_deg: Optional[float] = None
    detected_date: str
    evidence_notes: Optional[str] = None
    data_classification: str
    coordinates: Optional[Any] = None


class PollutantReading(BaseModel):
    id: str
    pollutant: str
    concentration_value: float
    unit: str
    averaging_period: str
    observed_at: str
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    data_classification: str
    monitoring_station: Optional[str] = None


class IndustrialEvidenceResponse(BaseModel):
    hotspot_id: str
    facility_name: str
    pollutant: str
    satellite_scene: str
    atmospheric_column_value: float
    unit: str
    wind_direction_degrees: float
    wind_speed_ms: float
    downwind_plume_alignment: bool
    nearest_monitoring_reading: Optional[float] = None
    evidence_statement: str
    limitations: str

