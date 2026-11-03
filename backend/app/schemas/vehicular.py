"""
THERMOS AI - Vehicular Emission Intelligence Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VehicularSummaryResponse(BaseModel):
    region_name: str
    monitored_road_segments_count: int
    high_emission_corridors_count: int
    mean_nox_emission_g_km_day: float
    mean_co2_emission_kg_km_day: float
    mean_pm_emission_g_km_day: float
    peak_emission_corridor: Optional[str] = None
    dataset_source: str = "CHETNA-Road (Mittakola et al. 2025)"
    data_classification: str = "modelled"
    limitations: str


class RoadSegmentResponse(BaseModel):
    id: str
    osm_id: Optional[str] = None
    name: str
    road_type: str
    length_m: Optional[float] = None
    lanes: int
    speed_limit_kmh: Optional[int] = None
    latest_nox_g_km_day: Optional[float] = None
    latest_co2_kg_km_day: Optional[float] = None


class VehicularHotspotItem(BaseModel):
    id: str
    hotspot_code: Optional[str] = None
    road_name: Optional[str] = None
    road_segment_id: Optional[str] = None
    pollutant: str
    emission_intensity: float
    unit: str
    severity: str
    detected_date: str
    traffic_context: Optional[str] = None
    data_classification: str


class VehicularTimeseriesPoint(BaseModel):
    date: str
    nox_g_km_day: float
    co2_kg_km_day: float
    pm_g_km_day: float
    road_name: str

