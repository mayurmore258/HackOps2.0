"""
THERMOS AI - Incident Reporting and Corrective Action Management Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    title: str = Field(..., description="Short incident summary")
    description: str = Field(..., description="Full factual description of the environmental concern")
    category: str = Field(..., description="air_pollution, industrial_emission, heat_wave, unauthorized_burning, odour, noise")
    severity: str = Field(default="medium", description="low, medium, high, critical")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_contact: Optional[str] = None
    reporter_type: str = Field(default="citizen", description="citizen, inspector, automated_hotspot, authority")


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    changed_by: Optional[str] = "analyst"
    status_comment: Optional[str] = None


class CorrectiveActionCreate(BaseModel):
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Technical instructions for corrective action")
    action_type: str = Field(..., description="site_inspection, stack_sampling, dust_suppression, traffic_diversion, green_buffer, regulatory_notice")
    priority: str = Field(default="medium", description="low, medium, high, urgent")
    assigned_to: str = Field(..., description="Designated official or response team")
    assigned_department: str = Field(default="Municipal Corporation / Pollution Control Board")
    due_date: Optional[str] = None


class CorrectiveActionUpdate(BaseModel):
    status: str = Field(..., description="assigned, in_progress, completed, verified, cancelled")
    completion_notes: Optional[str] = None
    verified_by: Optional[str] = None


class CorrectiveActionResponse(BaseModel):
    id: str
    incident_id: str
    title: str
    description: str
    action_type: str
    priority: str
    assigned_to: str
    assigned_department: str
    due_date: Optional[str] = None
    status: str
    completion_notes: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None


class StatusHistoryItem(BaseModel):
    from_status: str
    to_status: str
    changed_by: str
    comment: Optional[str] = None
    changed_at: str


class IncidentResponse(BaseModel):
    id: str
    incident_number: str
    title: str
    description: str
    category: str
    severity: str
    status: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_type: str
    reported_at: str
    environmental_context: Optional[Dict[str, Any]] = None
    corrective_actions: List[CorrectiveActionResponse] = Field(default_factory=list)
    status_history: List[StatusHistoryItem] = Field(default_factory=list)


class IncidentAnalyseRequest(BaseModel):
    buffer_radius_meters: float = Field(default=2000.0, description="Spatial search radius around incident point in meters")


class IncidentAnalyseResponse(BaseModel):
    incident_id: str
    nearby_heat_hotspots: List[Dict[str, Any]]
    nearby_industrial_facilities: List[Dict[str, Any]]
    nearby_vehicular_corridors: List[Dict[str, Any]]
    applicable_standards: List[Dict[str, Any]]
    nearest_compound_hotspot: Optional[Dict[str, Any]] = None
    technical_summary: str
    causation_disclaimer: str

