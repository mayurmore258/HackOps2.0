"""
THERMOS AI - Community Exposure Screening API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.community.service import CommunityExposureService
from app.schemas.common import ResponseEnvelope, ResponseMetadata
from app.schemas.community import (
    CommunitySummaryResponse,
    AreaExposureItem,
    SensitiveLocationItem,
)

router = APIRouter(prefix="/community", tags=["Community Exposure & Vulnerability"])


@router.get("/summary", response_model=ResponseEnvelope[CommunitySummaryResponse])
def get_community_summary(db: Session = Depends(get_db)):
    """Retrieve community-level exposure overview, exposed population, and vulnerability metrics."""
    data = CommunityExposureService.get_community_summary(db)
    return ResponseEnvelope(
        success=True,
        data=CommunitySummaryResponse(**data),
        metadata=ResponseMetadata(
            source="GHS-POP / WorldPop & Health Infrastructure Registry",
            classification="estimated"
        )
    )


@router.get("/exposure", response_model=ResponseEnvelope[List[AreaExposureItem]])
def list_exposure_assessments(db: Session = Depends(get_db)):
    """List ward-level hazard, exposure, and vulnerability screening indexes."""
    assessments = CommunityExposureService.list_exposure_assessments(db)
    items = [AreaExposureItem(**a) for a in assessments]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="Community Exposure Assessment Engine", classification="estimated")
    )


@router.get("/sensitive-locations", response_model=ResponseEnvelope[List[SensitiveLocationItem]])
def list_sensitive_locations(
    category: Optional[str] = Query(None, description="hospital, school, park, elder_care"),
    db: Session = Depends(get_db)
):
    """List sensitive receptors (schools, hospitals, parks) and their distance to hotspots."""
    locations = CommunityExposureService.list_sensitive_locations(db, category)
    items = [SensitiveLocationItem(**l) for l in locations]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="Municipal Sensitive Infrastructure Registry", classification="measured")
    )


@router.get("/areas/{area_id}", response_model=ResponseEnvelope[AreaExposureItem])
def get_area_exposure(
    area_id: str = Path(..., description="Administrative Area ID or Code"),
    db: Session = Depends(get_db)
):
    """Retrieve detailed exposure and vulnerability breakdown for a specific administrative ward."""
    data = CommunityExposureService.get_area_exposure(db, area_id)
    return ResponseEnvelope(
        success=True,
        data=AreaExposureItem(**data),
        metadata=ResponseMetadata(source="Ward Exposure Screening Dossier", classification="estimated")
    )


@router.post("/analyse", response_model=ResponseEnvelope[List[AreaExposureItem]])
def run_community_analysis(db: Session = Depends(get_db)):
    """Re-compute spatial intersection of population grids with active compound hotspots."""
    assessments = CommunityExposureService.list_exposure_assessments(db)
    items = [AreaExposureItem(**a) for a in assessments]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="Dynamic Spatial Exposure Engine", classification="estimated")
    )

