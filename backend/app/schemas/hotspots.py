"""
THERMOS AI - Compound Hotspot Intelligence Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HotspotWeightsConfig(BaseModel):
    """Configurable weights for compound risk calculation (summing to 1.0)."""
    heat_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    industrial_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    vehicular_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    exposure_weight: float = Field(default=0.20, ge=0.0, le=1.0)


class CompoundHotspotItem(BaseModel):
    id: str
    hotspot_code: str
    title: str
    region_name: str
    heat_score: float = Field(..., ge=0.0, le=100.0)
    industrial_score: float = Field(..., ge=0.0, le=100.0)
    vehicular_score: float = Field(..., ge=0.0, le=100.0)
    exposure_score: float = Field(..., ge=0.0, le=100.0)
    compound_risk_score: float = Field(..., ge=0.0, le=100.0)
    severity: str  # low, moderate, high, critical
    primary_hazard: str
    area_sqkm: Optional[float] = None
    detected_date: str
    methodology_version: str
    contributing_evidence: Dict[str, Any]
    limitations: str
    data_classification: str
    geometry: Optional[Any] = None


class CompoundHotspotSummaryResponse(BaseModel):
    total_compound_hotspots: int
    critical_count: int
    high_count: int
    moderate_count: int
    low_count: int
    mean_compound_risk_score: float
    predominant_hazard_cluster: str
    weights_used: HotspotWeightsConfig
    methodology_version: str


class HotspotsAnalyseRequest(BaseModel):
    region_id: Optional[str] = None
    weights: Optional[HotspotWeightsConfig] = None
    min_compound_score: Optional[float] = Field(default=40.0, ge=0.0, le=100.0)
    severity_filter: Optional[str] = None

