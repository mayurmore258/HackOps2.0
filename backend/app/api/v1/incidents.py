"""
THERMOS AI - Incident Reporting and Corrective Action API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.incidents.service import IncidentService
from app.schemas.common import ResponseEnvelope, ResponseMetadata, PaginationMeta
from app.schemas.incidents import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    CorrectiveActionCreate,
    CorrectiveActionUpdate,
    CorrectiveActionResponse,
    StatusHistoryItem,
    IncidentAnalyseRequest,
    IncidentAnalyseResponse,
)

router = APIRouter(prefix="/incidents", tags=["Incident & Corrective Action Management"])


def _to_incident_response(inc) -> IncidentResponse:
    actions = [
        CorrectiveActionResponse(
            id=str(a.id),
            incident_id=str(a.incident_id),
            title=a.title,
            description=a.description,
            action_type=a.action_type,
            priority=a.priority,
            assigned_to=a.assigned_to,
            assigned_department=a.assigned_department,
            due_date=a.due_date.isoformat() if a.due_date else None,
            status=a.status,
            completion_notes=a.completion_notes,
            verified_by=a.verified_by,
            verified_at=a.verified_at.isoformat() if a.verified_at else None
        )
        for a in inc.corrective_actions
    ]
    history = [
        StatusHistoryItem(
            from_status=h.from_status,
            to_status=h.to_status,
            changed_by=h.changed_by,
            comment=h.comment,
            changed_at=h.changed_at.isoformat()
        )
        for h in inc.status_history
    ]
    return IncidentResponse(
        id=str(inc.id),
        incident_number=inc.incident_number,
        title=inc.title,
        description=inc.description,
        category=inc.category,
        severity=inc.severity,
        status=inc.status,
        latitude=inc.latitude,
        longitude=inc.longitude,
        address=inc.address,
        reporter_name=inc.reporter_name,
        reporter_type=inc.reporter_type,
        reported_at=inc.reported_at.isoformat(),
        environmental_context=inc.environmental_context,
        corrective_actions=actions,
        status_history=history
    )


@router.post("", response_model=ResponseEnvelope[IncidentResponse])
def create_incident(
    req: IncidentCreate,
    db: Session = Depends(get_db)
):
    """Log a new environmental incident or citizen grievance with automatic geographic indexing."""
    inc = IncidentService.create_incident(db, req)
    return ResponseEnvelope(
        success=True,
        data=_to_incident_response(inc),
        metadata=ResponseMetadata(source="Incident Intake Router", classification="measured")
    )


@router.get("", response_model=ResponseEnvelope[List[IncidentResponse]])
def list_incidents(
    status: Optional[str] = Query(None, description="reported, under_review, in_progress, resolved, closed"),
    category: Optional[str] = Query(None, description="industrial_emission, heat_wave, air_pollution, noise"),
    severity: Optional[str] = Query(None, description="low, medium, high, critical"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List environmental incidents and citizen complaints with filtering and pagination."""
    incidents, total = IncidentService.list_incidents(db, status, category, severity, limit, offset)
    items = [_to_incident_response(inc) for inc in incidents]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="Incident Management Registry",
            classification="measured",
            pagination=PaginationMeta.create(total=total, limit=limit, offset=offset)
        )
    )


@router.get("/{id}", response_model=ResponseEnvelope[IncidentResponse])
def get_incident(
    id: str = Path(..., description="Incident ID or Incident Number"),
    db: Session = Depends(get_db)
):
    """Retrieve full incident dossier including corrective actions and status transition history."""
    inc = IncidentService.get_incident_by_id(db, id)
    return ResponseEnvelope(
        success=True,
        data=_to_incident_response(inc),
        metadata=ResponseMetadata(source="Incident Management Registry", classification="measured")
    )


@router.patch("/{id}", response_model=ResponseEnvelope[IncidentResponse])
def update_incident(
    id: str = Path(..., description="Incident ID or Incident Number"),
    req: IncidentUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update incident status, severity, or notes with full audit logging."""
    inc = IncidentService.update_incident(db, id, req)
    return ResponseEnvelope(
        success=True,
        data=_to_incident_response(inc),
        metadata=ResponseMetadata(source="Incident Management Registry", classification="measured")
    )


@router.post("/{id}/analyse", response_model=ResponseEnvelope[IncidentAnalyseResponse])
def analyse_incident(
    id: str = Path(..., description="Incident ID or Incident Number"),
    req: IncidentAnalyseRequest = IncidentAnalyseRequest(),
    db: Session = Depends(get_db)
):
    """Synthesize multi-hazard environmental context (nearby facilities, thermal anomalies, standards)."""
    analysis = IncidentService.analyse_incident_context(db, id, req.buffer_radius_meters)
    return ResponseEnvelope(
        success=True,
        data=IncidentAnalyseResponse(**analysis),
        metadata=ResponseMetadata(
            source="Multi-Hazard Incident Context Synthesizer",
            classification="modelled"
        )
    )


@router.post("/{id}/actions", response_model=ResponseEnvelope[CorrectiveActionResponse])
def add_corrective_action(
    id: str = Path(..., description="Incident ID or Incident Number"),
    req: CorrectiveActionCreate = ...,
    db: Session = Depends(get_db)
):
    """Assign a corrective action (e.g. site inspection, warning notice, dust suppression)."""
    action = IncidentService.add_corrective_action(db, id, req)
    item = CorrectiveActionResponse(
        id=str(action.id),
        incident_id=str(action.incident_id),
        title=action.title,
        description=action.description,
        action_type=action.action_type,
        priority=action.priority,
        assigned_to=action.assigned_to,
        assigned_department=action.assigned_department,
        due_date=action.due_date.isoformat() if action.due_date else None,
        status=action.status,
        completion_notes=action.completion_notes,
        verified_by=action.verified_by,
        verified_at=action.verified_at.isoformat() if action.verified_at else None
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="Corrective Action Workflow", classification="measured")
    )


@router.patch("/actions/{action_id}", response_model=ResponseEnvelope[CorrectiveActionResponse])
def update_corrective_action(
    action_id: str = Path(..., description="Corrective Action ID"),
    req: CorrectiveActionUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update status, completion notes, or verification for a corrective action."""
    action = IncidentService.update_action(db, action_id, req)
    item = CorrectiveActionResponse(
        id=str(action.id),
        incident_id=str(action.incident_id),
        title=action.title,
        description=action.description,
        action_type=action.action_type,
        priority=action.priority,
        assigned_to=action.assigned_to,
        assigned_department=action.assigned_department,
        due_date=action.due_date.isoformat() if action.due_date else None,
        status=action.status,
        completion_notes=action.completion_notes,
        verified_by=action.verified_by,
        verified_at=action.verified_at.isoformat() if action.verified_at else None
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="Corrective Action Workflow", classification="measured")
    )


@router.post("/{id}/resolve", response_model=ResponseEnvelope[IncidentResponse])
def resolve_incident(
    id: str = Path(..., description="Incident ID or Incident Number"),
    db: Session = Depends(get_db)
):
    """Mark an incident as resolved following verified corrective action."""
    inc = IncidentService.update_incident(
        db, id, IncidentUpdate(status="resolved", status_comment="Incident verified and resolved by environmental team.")
    )
    return ResponseEnvelope(
        success=True,
        data=_to_incident_response(inc),
        metadata=ResponseMetadata(source="Incident Lifecycle Management", classification="measured")
    )


@router.get("/{id}/history", response_model=ResponseEnvelope[List[StatusHistoryItem]])
def get_incident_history(
    id: str = Path(..., description="Incident ID or Incident Number"),
    db: Session = Depends(get_db)
):
    """Retrieve full chronological status transition and audit history for an incident."""
    inc = IncidentService.get_incident_by_id(db, id)
    history = [
        StatusHistoryItem(
            from_status=h.from_status,
            to_status=h.to_status,
            changed_by=h.changed_by,
            comment=h.comment,
            changed_at=h.changed_at.isoformat()
        )
        for h in inc.status_history
    ]
    return ResponseEnvelope(
        success=True,
        data=history,
        metadata=ResponseMetadata(source="Incident Audit Trail", classification="measured")
    )
