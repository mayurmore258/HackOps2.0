"""
THERMOS AI - Regulatory Compliance Screening Service

Evaluates observations against official Indian environmental standards (CPCB / MPCB NAAQS 2009).
Strictly separates technical screening from official legal determinations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models.compliance import (
    EnvironmentalStandard,
    StandardThreshold,
    ComplianceAssessment,
    RegulatoryAuthority,
)
from app.schemas.compliance import ComplianceScreeningRequest, ComplianceReviewRequest

logger = get_logger(__name__)


class ComplianceScreeningService:
    """Evaluates parameter observations against compatible statutory limits."""

    @staticmethod
    def list_standards(db: Session) -> List[EnvironmentalStandard]:
        """List all enacted environmental standards with their thresholds."""
        return db.query(EnvironmentalStandard).filter(EnvironmentalStandard.is_active == True).all()

    @staticmethod
    def get_standard_by_id(db: Session, standard_id: str) -> EnvironmentalStandard:
        """Retrieve standard by ID or code."""
        std = db.query(EnvironmentalStandard).filter(EnvironmentalStandard.id == standard_id).first()
        if not std:
            std = db.query(EnvironmentalStandard).filter(EnvironmentalStandard.code == standard_id).first()
            if not std:
                raise ResourceNotFoundError("EnvironmentalStandard", standard_id)
        return std

    @staticmethod
    def screen_observation(
        db: Session,
        req: ComplianceScreeningRequest
    ) -> ComplianceAssessment:
        """
        Screen an observation against the most applicable standard threshold.
        Validates unit and averaging period compatibility before comparison.
        """
        # Look for matching standard threshold (e.g. NAAQS 2009 for the parameter)
        threshold = (
            db.query(StandardThreshold)
            .filter(
                StandardThreshold.parameter.ilike(req.parameter),
                StandardThreshold.averaging_period == req.averaging_period,
                StandardThreshold.area_category == req.area_category
            )
            .first()
        )
        
        if not threshold:
            # Fallback to matching parameter with default residential category
            threshold = (
                db.query(StandardThreshold)
                .filter(StandardThreshold.parameter.ilike(req.parameter))
                .first()
            )
            
        if not threshold:
            raise ValidationError(
                f"No statutory standard found for parameter '{req.parameter}' with averaging period '{req.averaging_period}'."
            )

        # Check unit compatibility
        if req.unit.lower() != threshold.unit.lower():
            # If comparing incompatible units (e.g., mol/m2 vs ug/m3)
            assessment = ComplianceAssessment(
                standard_threshold_id=threshold.id,
                monitoring_location_id=req.monitoring_location_id,
                facility_id=req.facility_id,
                parameter=req.parameter,
                observed_value=req.observed_value,
                unit=req.unit,
                averaging_period=req.averaging_period,
                threshold_value=threshold.limit_value,
                ratio_to_threshold=0.0,
                status="insufficient_evidence",
                assessment_notes=(
                    f"Unit mismatch: Observation is in '{req.unit}', while statutory standard is '{threshold.unit}'. "
                    "Satellite column densities (mol/m2) cannot be compared directly against ambient concentration limits (ug/m3)."
                )
            )
            db.add(assessment)
            db.commit()
            db.refresh(assessment)
            return assessment

        ratio = round(req.observed_value / threshold.limit_value, 3)
        if ratio > 1.0:
            status = "potential_exceedance"
            notes = (
                f"Observed {req.averaging_period} value ({req.observed_value} {req.unit}) exceeds statutory "
                f"threshold ({threshold.limit_value} {threshold.unit}) by {round((ratio - 1.0) * 100, 1)}%. "
                "Flagged for technical review."
            )
        else:
            status = "within_reference_limit"
            notes = (
                f"Observed {req.averaging_period} value ({req.observed_value} {req.unit}) is within statutory "
                f"reference limit ({threshold.limit_value} {threshold.unit})."
            )

        assessment = ComplianceAssessment(
            standard_threshold_id=threshold.id,
            monitoring_location_id=req.monitoring_location_id,
            facility_id=req.facility_id,
            parameter=req.parameter,
            observed_value=req.observed_value,
            unit=req.unit,
            averaging_period=req.averaging_period,
            threshold_value=threshold.limit_value,
            ratio_to_threshold=ratio,
            status=status,
            assessment_notes=notes
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    @staticmethod
    def list_assessments(
        db: Session,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ComplianceAssessment], int]:
        """List compliance screening assessments."""
        query = db.query(ComplianceAssessment)
        if status:
            query = query.filter(ComplianceAssessment.status == status)
        total = query.count()
        items = query.order_by(ComplianceAssessment.created_at.desc()).offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def get_assessment_by_id(db: Session, assessment_id: str) -> ComplianceAssessment:
        """Retrieve single compliance assessment."""
        ass = db.query(ComplianceAssessment).filter(ComplianceAssessment.id == assessment_id).first()
        if not ass:
            raise ResourceNotFoundError("ComplianceAssessment", assessment_id)
        return ass

    @staticmethod
    def review_assessment(
        db: Session,
        assessment_id: str,
        review: ComplianceReviewRequest
    ) -> ComplianceAssessment:
        """Submit human review decision on a screening assessment."""
        ass = db.query(ComplianceAssessment).filter(ComplianceAssessment.id == assessment_id).first()
        if not ass:
            raise ResourceNotFoundError("ComplianceAssessment", assessment_id)
            
        ass.reviewed_by = review.reviewer_name
        ass.reviewed_at = datetime.now(timezone.utc)
        ass.review_decision = review.decision
        ass.assessment_notes += f" | Human Review: {review.review_notes}"
        
        if review.decision == "confirmed_concern":
            ass.status = "potential_exceedance"
        elif review.decision == "false_alarm":
            ass.status = "within_reference_limit"
            
        db.commit()
        db.refresh(ass)
        return ass

