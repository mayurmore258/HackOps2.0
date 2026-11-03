"""
THERMOS AI - Urban Heat Intelligence Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HeatSummaryResponse(BaseModel):
    region_name: str
    latest_acquisition_date: Optional[str] = None
    mean_lst_celsius: float
    min_lst_celsius: float
    max_lst_celsius: float
    mean_ndvi: Optional[float] = None
    mean_ndbi: Optional[float] = None
    hotspots_count: int
    severe_hotspots_count: int
    sensor_platform: str
    data_classification: str
    limitations: str


class HeatHotspotItem(BaseModel):
    id: str
    hotspot_code: Optional[str] = None
    severity: str
    lst_celsius: float
    lst_anomaly_celsius: float
    ndvi: Optional[float] = None
    ndbi: Optional[float] = None
    area_sqkm: Optional[float] = None
    detected_date: str
    data_classification: str
    coordinates: Optional[Any] = None


class HeatTimeseriesPoint(BaseModel):
    date: str
    mean_lst_celsius: float
    min_lst_celsius: float
    max_lst_celsius: float
    ndvi: Optional[float] = None
    sensor: str


class HeatIndicesResponse(BaseModel):
    region: str
    mean_ndvi: float = Field(..., description="Normalized Difference Vegetation Index (-1 to 1)")
    mean_ndbi: float = Field(..., description="Normalized Difference Built-up Index (-1 to 1)")
    mean_ndmi: float = Field(..., description="Normalized Difference Moisture Index (-1 to 1)")
    correlation_lst_ndvi: float
    correlation_lst_ndbi: float
    vegetation_cooling_effect_celsius: float


class HeatAnalysisRequest(BaseModel):
    region_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    severity_filter: Optional[str] = None
    min_lst_celsius: Optional[float] = None

