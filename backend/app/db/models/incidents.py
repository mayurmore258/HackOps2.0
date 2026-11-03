"""
THERMOS AI - Incident Reporting, Workflow, Corrective Actions, and Audit Log Models
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.db.base import Base, UUIDMixin, TimestampMixin, SpatialGeometry


class Incident(Base, UUIDMixin, TimestampMixin):
    """
    Environmental incident or citizen report lifecycle entity.
    Workflow: Report -> Evidence -> Analyse -> Compare Against Standards -> Human Review -> Recommend -> Assign -> Track -> Resolve
    """
    __tablename__ = "incidents"

    incident_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # air_pollution, industrial_emission, heat_wave, unauthorized_burning, odour, noise
    severity = Column(String(20), default="medium", nullable=False, index=True)  # low, medium, high, critical
    
    # Lifecycle Status:
    # reported, under_review, evidence_required, analysis_completed, action_recommended, action_assigned, in_progress, resolved, closed, reopened
    status = Column(String(40), default="reported", nullable=False, index=True)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(Text, nullable=True)
    geom = Column(SpatialGeometry("POINT", srid=4326), nullable=True)
    
    # Reporter Details
    reporter_name = Column(String(100), nullable=True)
    reporter_contact = Column(String(100), nullable=True)
    reporter_type = Column(String(50), default="citizen", nullable=False)  # citizen, inspector, automated_hotspot, authority
    reported_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Environmental context snapshot
    environmental_context = Column(JSON, nullable=True)

    attachments = relationship("IncidentAttachment", back_populates="incident", cascade="all, delete-orphan")
    assessment = relationship("IncidentAssessment", uselist=False, back_populates="incident", cascade="all, delete-orphan")
    corrective_actions = relationship("CorrectiveAction", back_populates="incident", cascade="all, delete-orphan")
    status_history = relationship("IncidentStatusHistory", back_populates="incident", cascade="all, delete-orphan")


class IncidentAttachment(Base, UUIDMixin, TimestampMixin):
    """File attachment or sensor photo associated with an incident."""
    __tablename__ = "incident_attachments"

    incident_id = Column(UUIDMixin.id.type, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(200), nullable=False)
    file_type = Column(String(50), nullable=False)  # image/jpeg, application/pdf, text/csv
    file_uri = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="attachments")


class IncidentAssessment(Base, UUIDMixin, TimestampMixin):
    """Integrated multi-hazard analysis linking incident to hotspots, standards, and exposure."""
    __tablename__ = "incident_assessments"

    incident_id = Column(UUIDMixin.id.type, ForeignKey("incidents.id", ondelete="CASCADE"), unique=True, nullable=False)
    compound_hotspot_id = Column(UUIDMixin.id.type, ForeignKey("compound_hotspots.id", ondelete="SET NULL"), nullable=True)
    
    nearby_facilities_summary = Column(JSON, nullable=True)
    nearby_heat_summary = Column(JSON, nullable=True)
    nearby_vehicular_summary = Column(JSON, nullable=True)
    applicable_standards_summary = Column(JSON, nullable=True)
    
    technical_assessment_notes = Column(Text, nullable=False)
    potential_causes_statement = Column(Text, default="Proximity does not establish direct legal causation. Field sampling required.", nullable=False)
    reviewer_name = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    incident = relationship("Incident", back_populates="assessment")


class CorrectiveAction(Base, UUIDMixin, TimestampMixin):
    """Action item assigned to mitigate, inspect, or rectify an environmental concern."""
    __tablename__ = "corrective_actions"

    incident_id = Column(UUIDMixin.id.type, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)  # site_inspection, stack_sampling, dust_suppression, traffic_diversion, green_buffer, regulatory_notice
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, urgent
    assigned_to = Column(String(100), nullable=False)  # Department, officer, or agency
    assigned_department = Column(String(100), default="Municipal Corporation / Pollution Control Board", nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Lifecycle: assigned, in_progress, completed, verified, cancelled
    status = Column(String(30), default="assigned", nullable=False, index=True)
    
    completion_notes = Column(Text, nullable=True)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    incident = relationship("Incident", back_populates="corrective_actions")


class IncidentStatusHistory(Base, UUIDMixin, TimestampMixin):
    """Audit trail of status transitions for an incident."""
    __tablename__ = "incident_status_history"

    incident_id = Column(UUIDMixin.id.type, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(40), nullable=False)
    to_status = Column(String(40), nullable=False)
    changed_by = Column(String(100), default="system", nullable=False)
    comment = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("Incident", back_populates="status_history")


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """System-wide security and operations audit log."""
    __tablename__ = "audit_logs"

    actor = Column(String(100), default="system", nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, REVIEW, RUN_SIMULATION
    entity_type = Column(String(50), nullable=False, index=True)  # incident, scenario, compliance, model
    entity_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

