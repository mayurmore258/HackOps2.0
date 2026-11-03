"""
THERMOS AI - Industrial Pollution Intelligence API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.spatial import geometry_to_geojson_dict
from app.modules.industrial.service import IndustrialIntelligenceService
from app.schemas.common import (
    ResponseEnvelope,
    ResponseMetadata,
    PaginationParams,
    PaginationMeta,
)
from app.schemas.industrial import (
    IndustrialSummaryResponse,
    IndustrialFacilityResponse,
    IndustrialHotspotItem,
    PollutantReading,
    IndustrialEvidenceResponse,
)
from app.db.models.datasets import PollutantObservation

router = APIRouter(prefix="/industrial", tags=["Industrial Pollution Intelligence"])


@router.get("/summary", response_model=ResponseEnvelope[IndustrialSummaryResponse])
def get_industrial_summary(
    region_code: str = Query("PANVEL_NAVI_MUMBAI", description="Region code"),
    db: Session = Depends(get_db)
):
    """Retrieve industrial facility counts, Red/Orange categories, and atmospheric column indicators."""
    data = IndustrialIntelligenceService.get_industrial_summary(db, region_code)
    return ResponseEnvelope(
        success=True,
        data=IndustrialSummaryResponse(**data),
        metadata=ResponseMetadata(
            source="Copernicus Sentinel-5P TROPOMI & MPCB Consents",
            classification="satellite_derived",
            limitations=["Atmospheric column indicators are regional; do not prove legal violation of an individual facility."]
        )
    )


@router.get("/facilities", response_model=ResponseEnvelope[List[IndustrialFacilityResponse]])
def list_industrial_facilities(
    category: Optional[str] = Query(None, description="Red, Orange, Green"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List registered industrial manufacturing facilities and CEMS status."""
    facilities, total = IndustrialIntelligenceService.list_facilities(db, category, limit, offset)
    items = [
        IndustrialFacilityResponse(
            id=str(f.id),
            name=f.name,
            industry_type=f.industry_type,
            category=f.category,
            consent_id=f.consent_id,
            district=f.district,
            state=f.state,
            latitude=f.latitude,
            longitude=f.longitude,
            address=f.address,
            is_cems_connected=f.is_cems_connected
        )
        for f in facilities
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="MPCB Industrial Consent Registry",
            classification="measured",
            pagination=PaginationMeta.create(total=total, limit=limit, offset=offset)
        )
    )


@router.get("/hotspots", response_model=ResponseEnvelope[List[IndustrialHotspotItem]])
def list_industrial_hotspots(
    pollutant: Optional[str] = Query(None, description="SO2, NO2"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List potential industrial pollution indicator hotspots with wind alignment flags."""
    hotspots, total = IndustrialIntelligenceService.list_hotspots(db, pollutant, limit, offset)
    items = [
        IndustrialHotspotItem(
            id=str(h.id),
            hotspot_code=h.hotspot_code,
            facility_name=h.facility.name if h.facility else None,
            facility_id=str(h.facility_id) if h.facility_id else None,
            pollutant=h.pollutant,
            concentration_estimate=h.concentration_estimate,
            unit=h.unit,
            severity=h.severity,
            wind_aligned=h.wind_aligned,
            wind_direction_deg=h.wind_direction_deg,
            detected_date=h.detected_date.isoformat(),
            evidence_notes=h.evidence_notes,
            data_classification=h.data_classification,
            coordinates=geometry_to_geojson_dict(h.geom)
        )
        for h in hotspots
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="Sentinel-5P TROPOMI Atmospheric Column Engine",
            classification="satellite_derived",
            pagination=PaginationMeta.create(total=total, limit=limit, offset=offset)
        )
    )


@router.get("/pollutants", response_model=ResponseEnvelope[List[PollutantReading]])
def list_pollutant_readings(
    pollutant: Optional[str] = Query(None, description="SO2, NO2, PM2.5, PM10"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List ground and station monitored observations with wind vectors."""
    query = db.query(PollutantObservation)
    if pollutant:
        query = query.filter(PollutantObservation.pollutant == pollutant)
    readings = query.order_by(PollutantObservation.observed_at.desc()).limit(limit).all()
    
    items = [
        PollutantReading(
            id=str(p.id),
            pollutant=p.pollutant,
            concentration_value=p.concentration_value,
            unit=p.unit,
            averaging_period=p.averaging_period,
            observed_at=p.observed_at.isoformat(),
            wind_speed_ms=p.wind_speed_ms,
            wind_direction_deg=p.wind_direction_deg,
            data_classification=p.data_classification,
            monitoring_station=p.monitoring_location.name if p.monitoring_location else None
        )
        for p in readings
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="CPCB / MPCB CAAQMS Stations", classification="measured")
    )


@router.get("/evidence/{id}", response_model=ResponseEnvelope[IndustrialEvidenceResponse])
def get_industrial_evidence(
    id: str = Path(..., description="Hotspot ID or Code"),
    db: Session = Depends(get_db)
):
    """Retrieve explainable evidence dossier linking TROPOMI column, wind vector, and facility."""
    evidence = IndustrialIntelligenceService.get_evidence(db, id)
    return ResponseEnvelope(
        success=True,
        data=IndustrialEvidenceResponse(**evidence),
        metadata=ResponseMetadata(
            source="THERMOS AI Evidence Synthesis Engine",
            classification="satellite_derived",
            limitations=["Contextual evidence for regulatory investigation; not a formal legal citation."]
        )
    )


@router.post("/analyse", response_model=ResponseEnvelope[List[IndustrialHotspotItem]])
def run_industrial_analysis(
    pollutant: Optional[str] = Query("SO2"),
    db: Session = Depends(get_db)
):
    """Run dynamic wind-aligned industrial plume screening analysis."""
    hotspots, total = IndustrialIntelligenceService.list_hotspots(db, pollutant=pollutant, limit=50)
    items = [
        IndustrialHotspotItem(
            id=str(h.id),
            hotspot_code=h.hotspot_code,
            facility_name=h.facility.name if h.facility else None,
            facility_id=str(h.facility_id) if h.facility_id else None,
            pollutant=h.pollutant,
            concentration_estimate=h.concentration_estimate,
            unit=h.unit,
            severity=h.severity,
            wind_aligned=h.wind_aligned,
            wind_direction_deg=h.wind_direction_deg,
            detected_date=h.detected_date.isoformat(),
            evidence_notes=h.evidence_notes,
            data_classification=h.data_classification,
            coordinates=geometry_to_geojson_dict(h.geom)
        )
        for h in hotspots
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="TROPOMI Wind Dispersion Screening Engine",
            classification="satellite_derived"
        )
    )
