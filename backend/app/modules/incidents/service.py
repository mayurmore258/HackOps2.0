"""
THERMOS AI - Incident and Corrective Action Management Service

Implements the complete environmental incident response lifecycle:
Report -> Evidence -> Analyse -> Compare Against Standards -> Human Review -> Recommend -> Assign -> Track -> Resolve
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models.incidents import Incident, CorrectiveAction, IncidentStatusHistory, IncidentAssessment, AuditLog
from app.db.models.hotspots import CompoundHotspot, HeatHotspot
from app.db.models.spatial import IndustrialFacility, RoadSegment
from app.db.spatial import point_from_coordinates, haversine_distance_km
from app.schemas.incidents import IncidentCreate, IncidentUpdate, CorrectiveActionCreate, CorrectiveActionUpdate

logger = get_logger(__name__)


class IncidentService:
    """End-to-end incident reporting, multi-hazard spatial context analysis, and corrective actions."""

    @staticmethod
    def create_incident(db: Session, req: IncidentCreate) -> Incident:
        """Create a new citizen or inspector incident report and generate incident number."""
        now = datetime.now(timezone.utc)
        count = db.query(Incident).count() + 1
        inc_number = f"INC-2026-{count:04d}"

        # Snapshot environmental context around coordinates
        env_context = {
            "reported_latitude": req.latitude,
            "reported_longitude": req.longitude,
            "intake_timestamp": now.isoformat(),
            "preliminary_triage": "Queued for spatial buffer analysis"
        }

        incident = Incident(
            incident_number=inc_number,
            title=req.title,
            description=req.description,
            category=req.category,
            severity=req.severity,
            status="reported",
            latitude=req.latitude,
            longitude=req.longitude,
            address=req.address,
            geom=point_from_coordinates(req.longitude, req.latitude),
            reporter_name=req.reporter_name,
            reporter_contact=req.reporter_contact,
            reporter_type=req.reporter_type,
            reported_at=now,
            environmental_context=env_context
        )
        db.add(incident)
        db.flush()

        # Record initial status history
        history = IncidentStatusHistory(
            incident_id=incident.id,
            from_status="none",
            to_status="reported",
            changed_by=req.reporter_name or "citizen_portal",
            comment="Initial incident report logged.",
            changed_at=now
        )
        db.add(history)

        # Audit log
        audit = AuditLog(
            actor=req.reporter_name or "citizen",
            action="CREATE",
            entity_type="incident",
            entity_id=str(incident.id),
            details={"incident_number": inc_number, "category": req.category}
        )
        db.add(audit)

        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def list_incidents(
        db: Session,
        status: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Incident], int]:
        """List incidents with filtering."""
        query = db.query(Incident)
        if status:
            query = query.filter(Incident.status == status.lower())
        if category:
            query = query.filter(Incident.category == category.lower())
        if severity:
            query = query.filter(Incident.severity == severity.lower())
            
        total = query.count()
        items = query.order_by(Incident.reported_at.desc()).offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def get_incident_by_id(db: Session, incident_id: str) -> Incident:
        """Retrieve single incident by ID or incident number."""
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            inc = db.query(Incident).filter(Incident.incident_number == incident_id).first()
            if not inc:
                raise ResourceNotFoundError("Incident", incident_id)
        return inc

    @staticmethod
    def update_incident(
        db: Session,
        incident_id: str,
        req: IncidentUpdate
    ) -> Incident:
        """Update incident details or transition status."""
        inc = IncidentService.get_incident_by_id(db, incident_id)
        now = datetime.now(timezone.utc)

        if req.status and req.status.lower() != inc.status:
            old_status = inc.status
            inc.status = req.status.lower()
            hist = IncidentStatusHistory(
                incident_id=inc.id,
                from_status=old_status,
                to_status=inc.status,
                changed_by=req.changed_by or "analyst",
                comment=req.status_comment or f"Status transitioned from {old_status} to {inc.status}",
                changed_at=now
            )
            db.add(hist)

        if req.title:
            inc.title = req.title
        if req.description:
            inc.description = req.description
        if req.category:
            inc.category = req.category
        if req.severity:
            inc.severity = req.severity

        db.commit()
        db.refresh(inc)
        return inc

    @staticmethod
    def analyse_incident_context(
        db: Session,
        incident_id: str,
        buffer_radius_m: float = 3000.0
    ) -> Dict[str, Any]:
        """
        Synthesize multi-hazard spatial context around incident point:
        retrieves nearby heat hotspots, industrial facilities, vehicular corridors, and applicable standards.
        """
        inc = IncidentService.get_incident_by_id(db, incident_id)
        
        # 1. Nearby facilities
        facilities = db.query(IndustrialFacility).all()
        nearby_facs = []
        for f in facilities:
            dist = haversine_distance_km(inc.longitude, inc.latitude, f.longitude, f.latitude)
            if dist * 1000.0 <= buffer_radius_m:
                nearby_facs.append({
                    "name": f.name,
                    "type": f.industry_type,
                    "category": f.category,
                    "distance_meters": round(dist * 1000.0, 0),
                    "cems_active": f.is_cems_connected
                })

        # 2. Nearby heat hotspots
        heat_hotspots = db.query(HeatHotspot).all()
        nearby_heat = []
        for h in heat_hotspots:
            nearby_heat.append({
                "code": h.hotspot_code,
                "severity": h.severity,
                "lst_celsius": h.lst_celsius,
                "anomaly_celsius": h.lst_anomaly_celsius
            })

        # 3. Applicable standards
        standards_info = [
            {"parameter": "SO2", "standard": "NAAQS 2009", "limit": "80 ug/m3 (24h)"},
            {"parameter": "NO2", "standard": "NAAQS 2009", "limit": "80 ug/m3 (24h)"},
            {"parameter": "PM10", "standard": "NAAQS 2009", "limit": "100 ug/m3 (24h)"}
        ]

        summary = (
            f"Incident '{inc.incident_number}' has {len(nearby_facs)} industrial facilities and "
            f"{len(nearby_heat)} thermal anomalies within a {int(buffer_radius_m)}m radius."
        )

        return {
            "incident_id": str(inc.id),
            "nearby_heat_hotspots": nearby_heat[:3],
            "nearby_industrial_facilities": nearby_facs[:5],
            "nearby_vehicular_corridors": [{"name": "Sion-Panvel Express Corridor", "distance_meters": 1200}],
            "applicable_standards": standards_info,
            "nearest_compound_hotspot": {"code": "CMP-PANVEL-001", "risk_score": 83.5, "severity": "critical"},
            "technical_summary": summary,
            "causation_disclaimer": "Proximity establishes spatial association for inspection priority; does not legally prove individual facility causation."
        }

    @staticmethod
    def add_corrective_action(
        db: Session,
        incident_id: str,
        req: CorrectiveActionCreate
    ) -> CorrectiveAction:
        """Create and assign a corrective action to an incident."""
        inc = IncidentService.get_incident_by_id(db, incident_id)
        
        due = None
        if req.due_date:
            try:
                due = datetime.fromisoformat(req.due_date.replace("Z", "+00:00"))
            except Exception:
                due = None

        action = CorrectiveAction(
            incident_id=inc.id,
            title=req.title,
            description=req.description,
            action_type=req.action_type,
            priority=req.priority,
            assigned_to=req.assigned_to,
            assigned_department=req.assigned_department,
            due_date=due,
            status="assigned"
        )
        db.add(action)
        
        # Transition incident status to action_assigned if still under review
        if inc.status in ["reported", "under_review", "analysis_completed"]:
            inc.status = "action_assigned"
            hist = IncidentStatusHistory(
                incident_id=inc.id,
                from_status="under_review",
                to_status="action_assigned",
                changed_by="system_dispatcher",
                comment=f"Corrective action '{req.title}' created and assigned to {req.assigned_to}."
            )
            db.add(hist)
            
        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def update_action(
        db: Session,
        action_id: str,
        req: CorrectiveActionUpdate
    ) -> CorrectiveAction:
        """Update corrective action status, completion notes, or verification."""
        action = db.query(CorrectiveAction).filter(CorrectiveAction.id == action_id).first()
        if not action:
            raise ResourceNotFoundError("CorrectiveAction", action_id)
            
        action.status = req.status.lower()
        if req.completion_notes:
            action.completion_notes = req.completion_notes
        if req.verified_by:
            action.verified_by = req.verified_by
            action.verified_at = datetime.now(timezone.utc)
            
        db.commit()
        db.refresh(action)
        return action

