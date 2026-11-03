"""
THERMOS AI - Dashboard Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HotspotCounts(BaseModel):
    heat_hotspots: int = 0
    industrial_hotspots: int = 0
    vehicular_hotspots: int = 0
    compound_hotspots: int = 0
    critical_compound_hotspots: int = 0


class HighRiskLocation(BaseModel):
    hotspot_id: str
    code: str
    title: str
    region: str
    compound_risk_score: float
    severity: str
    primary_hazard: str
    exposed_population: Optional[int] = None


class RecentIncidentSummary(BaseModel):
    id: str
    incident_number: str
    title: str
    category: str
    severity: str
    status: str
    reported_at: str


class DatasetFreshness(BaseModel):
    dataset_name: str
    classification: str
    last_updated: Optional[str] = None
    records_count: int = 0
    status: str = "operational"


class DashboardSummaryResponse(BaseModel):
    """Integrated high-level environmental snapshot for executive dashboards."""
    pilot_region: str
    hotspot_counts: HotspotCounts
    high_risk_locations: List[HighRiskLocation]
    recent_incidents: List[RecentIncidentSummary]
    dataset_freshness: List[DatasetFreshness]
    active_interventions_count: int = 0
    open_compliance_screenings_count: int = 0
    overall_environmental_health_index: float = Field(
        ...,
        description="Region-wide screening index (0-100, higher indicates greater cumulative pressure)"
    )

