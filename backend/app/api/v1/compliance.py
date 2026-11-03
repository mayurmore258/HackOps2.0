"""
THERMOS AI - Regulatory Compliance API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.compliance.service import ComplianceScreeningService
from app.schemas.common import ResponseEnvelope, ResponseMetadata, PaginationMeta
from app.schemas.compliance import (
    EnvironmentalStandardResponse,
    StandardThresholdResponse,
    ComplianceScreeningRequest,
    ComplianceAssessmentResponse,
    ComplianceReviewRequest,
)

router = APIRouter(prefix="/compliance", tags=["Regulatory Compliance Screening"])


@router.get("/standards", response_model=ResponseEnvelope[List[EnvironmentalStandardResponse]])
def list_standards(db: Session = Depends(get_db)):
    """List official regulatory standards (e.g. CPCB NAAQS 2009) and statutory thresholds."""
    standards = ComplianceScreeningService.list_standards(db)
    items = []
    for s in standards:
        th_items = [
            StandardThresholdResponse(
                id=str(t.id),
                parameter=t.parameter,
                limit_value=t.limit_value,
                unit=t.unit,
                averaging_period=t.averaging_period,
                area_category=t.area_category,
                sampling_method=t.sampling_method,
                applicability_clause=t.applicability_clause
            )
            for t in s.thresholds
        ]
        items.append(EnvironmentalStandardResponse(
            id=str(s.id),
            authority_name=s.authority.name if s.authority else "CPCB",
            code=s.code,
            title=s.title,
            document_identifier=s.document_identifier,
            category=s.category,
            source_url=s.source_url,
            summary=s.summary,
            thresholds=th_items
        ))
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="Official Indian Environmental Standards", classification="measured")
    )


@router.get("/standards/{id}", response_model=ResponseEnvelope[EnvironmentalStandardResponse])
def get_standard(
    id: str = Path(..., description="Standard ID or Code"),
    db: Session = Depends(get_db)
):
    """Retrieve full text metadata and limit thresholds for a specific standard."""
    s = ComplianceScreeningService.get_standard_by_id(db, id)
    th_items = [
        StandardThresholdResponse(
            id=str(t.id),
            parameter=t.parameter,
            limit_value=t.limit_value,
            unit=t.unit,
            averaging_period=t.averaging_period,
            area_category=t.area_category,
            sampling_method=t.sampling_method,
            applicability_clause=t.applicability_clause
        )
        for t in s.thresholds
    ]
    item = EnvironmentalStandardResponse(
        id=str(s.id),
        authority_name=s.authority.name if s.authority else "CPCB",
        code=s.code,
        title=s.title,
        document_identifier=s.document_identifier,
        category=s.category,
        source_url=s.source_url,
        summary=s.summary,
        thresholds=th_items
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="Statutory Standards Document", classification="measured")
    )


@router.get("/assessments", response_model=ResponseEnvelope[List[ComplianceAssessmentResponse]])
def list_assessments(
    status: Optional[str] = Query(None, description="potential_exceedance, within_reference_limit, insufficient_evidence"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List compliance screening results against applicable standards."""
    assessments, total = ComplianceScreeningService.list_assessments(db, status, limit, offset)
    items = [
        ComplianceAssessmentResponse(
            id=str(a.id),
            parameter=a.parameter,
            observed_value=a.observed_value,
            unit=a.unit,
            averaging_period=a.averaging_period,
            threshold_value=a.threshold_value,
            ratio_to_threshold=a.ratio_to_threshold,
            status=a.status,
            standard_title=a.standard_threshold.standard.title if (a.standard_threshold and a.standard_threshold.standard) else "NAAQS 2009",
            authority=a.standard_threshold.standard.authority.name if (a.standard_threshold and a.standard_threshold.standard and a.standard_threshold.standard.authority) else "CPCB",
            assessment_notes=a.assessment_notes,
            limitations=a.limitations,
            reviewed_by=a.reviewed_by,
            reviewed_at=a.reviewed_at.isoformat() if a.reviewed_at else None,
            review_decision=a.review_decision
        )
        for a in assessments
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="Compliance Screening Engine",
            classification="measured",
            pagination=PaginationMeta.create(total=total, limit=limit, offset=offset)
        )
    )


@router.get("/assessments/{id}", response_model=ResponseEnvelope[ComplianceAssessmentResponse])
def get_assessment(
    id: str = Path(..., description="Assessment ID"),
    db: Session = Depends(get_db)
):
    """Retrieve details of a single compliance screening assessment."""
    a = ComplianceScreeningService.get_assessment_by_id(db, id)
    item = ComplianceAssessmentResponse(
        id=str(a.id),
        parameter=a.parameter,
        observed_value=a.observed_value,
        unit=a.unit,
        averaging_period=a.averaging_period,
        threshold_value=a.threshold_value,
        ratio_to_threshold=a.ratio_to_threshold,
        status=a.status,
        standard_title=a.standard_threshold.standard.title if (a.standard_threshold and a.standard_threshold.standard) else "NAAQS 2009",
        authority=a.standard_threshold.standard.authority.name if (a.standard_threshold and a.standard_threshold.standard and a.standard_threshold.standard.authority) else "CPCB",
        assessment_notes=a.assessment_notes,
        limitations=a.limitations,
        reviewed_by=a.reviewed_by,
        reviewed_at=a.reviewed_at.isoformat() if a.reviewed_at else None,
        review_decision=a.review_decision
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="Compliance Screening Engine", classification="measured")
    )


@router.post("/assessments", response_model=ResponseEnvelope[ComplianceAssessmentResponse])
def screen_observation(
    req: ComplianceScreeningRequest,
    db: Session = Depends(get_db)
):
    """Screen an environmental observation against statutory standards and return transparent evaluation."""
    a = ComplianceScreeningService.screen_observation(db, req)
    item = ComplianceAssessmentResponse(
        id=str(a.id),
        parameter=a.parameter,
        observed_value=a.observed_value,
        unit=a.unit,
        averaging_period=a.averaging_period,
        threshold_value=a.threshold_value,
        ratio_to_threshold=a.ratio_to_threshold,
        status=a.status,
        standard_title=a.standard_threshold.standard.title if (a.standard_threshold and a.standard_threshold.standard) else "NAAQS 2009",
        authority=a.standard_threshold.standard.authority.name if (a.standard_threshold and a.standard_threshold.standard and a.standard_threshold.standard.authority) else "CPCB",
        assessment_notes=a.assessment_notes,
        limitations=a.limitations,
        reviewed_by=a.reviewed_by,
        reviewed_at=a.reviewed_at.isoformat() if a.reviewed_at else None,
        review_decision=a.review_decision
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="Compliance Screening Engine", classification="measured")
    )


@router.post("/assessments/{id}/review", response_model=ResponseEnvelope[ComplianceAssessmentResponse])
def review_assessment(
    id: str = Path(..., description="Assessment ID"),
    review: ComplianceReviewRequest = ...,
    db: Session = Depends(get_db)
):
    """Submit authorized human reviewer determination on a compliance screening."""
    a = ComplianceScreeningService.review_assessment(db, id, review)
    item = ComplianceAssessmentResponse(
        id=str(a.id),
        parameter=a.parameter,
        observed_value=a.observed_value,
        unit=a.unit,
        averaging_period=a.averaging_period,
        threshold_value=a.threshold_value,
        ratio_to_threshold=a.ratio_to_threshold,
        status=a.status,
        standard_title=a.standard_threshold.standard.title if (a.standard_threshold and a.standard_threshold.standard) else "NAAQS 2009",
        authority=a.standard_threshold.standard.authority.name if (a.standard_threshold and a.standard_threshold.standard and a.standard_threshold.standard.authority) else "CPCB",
        assessment_notes=a.assessment_notes,
        limitations=a.limitations,
        reviewed_by=a.reviewed_by,
        reviewed_at=a.reviewed_at.isoformat() if a.reviewed_at else None,
        review_decision=a.review_decision
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="Human Regulatory Review Decision", classification="measured")
    )
