"""
THERMOS AI - Compound Hotspots API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.spatial import geometry_to_geojson_dict
from app.modules.risk.service import CompoundHotspotService
from app.schemas.common import (
    ResponseEnvelope,
    ResponseMetadata,
    PaginationMeta,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)
from app.schemas.hotspots import (
    CompoundHotspotItem,
    CompoundHotspotSummaryResponse,
    HotspotWeightsConfig,
    HotspotsAnalyseRequest,
)

router = APIRouter(prefix="/hotspots", tags=["Compound Hotspot Intelligence"])


@router.get("/summary", response_model=ResponseEnvelope[CompoundHotspotSummaryResponse])
def get_compound_hotspots_summary(
    region_code: str = Query("PANVEL_NAVI_MUMBAI", description="Region code"),
    db: Session = Depends(get_db)
):
    """Retrieve statistical breakdown of multi-hazard compound hotspots."""
    data = CompoundHotspotService.get_summary(db, region_code)
    return ResponseEnvelope(
        success=True,
        data=CompoundHotspotSummaryResponse(**data),
        metadata=ResponseMetadata(
            source="ThermoSim Compound Intelligence Engine",
            classification="modelled",
            limitations=["Screening score normalizes incompatible units into a 0-100 index for intervention prioritisation."]
        )
    )


@router.get("/compound", response_model=ResponseEnvelope[List[CompoundHotspotItem]])
def list_compound_hotspots(
    severity: Optional[str] = Query(None, description="critical, high, moderate, low"),
    min_score: Optional[float] = Query(None, description="Minimum compound score (0-100)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List compound hotspots with component scores (Heat, Industrial, Vehicular, Exposure)."""
    hotspots, total = CompoundHotspotService.list_compound_hotspots(db, severity, min_score, limit, offset)
    items = [
        CompoundHotspotItem(
            id=str(h.id),
            hotspot_code=h.hotspot_code,
            title=h.title,
            region_name=h.region.name if h.region else "Panvel and Navi Mumbai",
            heat_score=h.heat_score,
            industrial_score=h.industrial_score,
            vehicular_score=h.vehicular_score,
            exposure_score=h.exposure_score,
            compound_risk_score=h.compound_risk_score,
            severity=h.severity,
            primary_hazard=h.primary_hazard,
            area_sqkm=h.area_sqkm,
            detected_date=h.detected_date.isoformat(),
            methodology_version=h.methodology_version,
            contributing_evidence=h.contributing_evidence,
            limitations=h.limitations,
            data_classification=h.data_classification,
            geometry=geometry_to_geojson_dict(h.geom)
        )
        for h in hotspots
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="ThermoSim Compound Engine",
            classification="modelled",
            pagination=PaginationMeta.create(total=total, limit=limit, offset=offset)
        )
    )


@router.get("/layers", response_model=ResponseEnvelope[GeoJSONFeatureCollection])
def get_compound_geojson_layers(
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Export compound risk hotspot boundaries as GeoJSON FeatureCollection."""
    hotspots, _ = CompoundHotspotService.list_compound_hotspots(db, severity=severity, limit=100)
    features = []
    for h in hotspots:
        geom = geometry_to_geojson_dict(h.geom)
        if geom:
            features.append(GeoJSONFeature(
                id=str(h.id),
                geometry=geom,
                properties={
                    "hotspot_code": h.hotspot_code,
                    "title": h.title,
                    "compound_risk_score": h.compound_risk_score,
                    "severity": h.severity,
                    "primary_hazard": h.primary_hazard,
                    "heat_score": h.heat_score,
                    "industrial_score": h.industrial_score,
                    "vehicular_score": h.vehicular_score,
                    "exposure_score": h.exposure_score,
                    "classification": "modelled"
                }
            ))
    return ResponseEnvelope(
        success=True,
        data=GeoJSONFeatureCollection(features=features),
        metadata=ResponseMetadata(source="ThermoSim GeoEngine", classification="modelled")
    )


@router.get("/{hotspot_id}", response_model=ResponseEnvelope[CompoundHotspotItem])
def get_compound_hotspot(
    hotspot_id: str = Path(..., description="Hotspot ID or Code"),
    db: Session = Depends(get_db)
):
    """Retrieve full detail and contributing evidence for a specific compound hotspot."""
    h = CompoundHotspotService.get_hotspot_by_id(db, hotspot_id)
    item = CompoundHotspotItem(
        id=str(h.id),
        hotspot_code=h.hotspot_code,
        title=h.title,
        region_name=h.region.name if h.region else "Panvel and Navi Mumbai",
        heat_score=h.heat_score,
        industrial_score=h.industrial_score,
        vehicular_score=h.vehicular_score,
        exposure_score=h.exposure_score,
        compound_risk_score=h.compound_risk_score,
        severity=h.severity,
        primary_hazard=h.primary_hazard,
        area_sqkm=h.area_sqkm,
        detected_date=h.detected_date.isoformat(),
        methodology_version=h.methodology_version,
        contributing_evidence=h.contributing_evidence,
        limitations=h.limitations,
        data_classification=h.data_classification,
        geometry=geometry_to_geojson_dict(h.geom)
    )
    return ResponseEnvelope(
        success=True,
        data=item,
        metadata=ResponseMetadata(source="ThermoSim Hotspot Registry", classification="modelled")
    )


@router.post("/analyse", response_model=ResponseEnvelope[List[CompoundHotspotItem]])
def recalculate_compound_analysis(
    req: HotspotsAnalyseRequest,
    db: Session = Depends(get_db)
):
    """Dynamically re-evaluate compound hotspots using custom user-defined weights."""
    hotspots, total = CompoundHotspotService.list_compound_hotspots(db, limit=50)
    items = []
    for h in hotspots:
        new_score, new_sev = CompoundHotspotService.calculate_compound_score(
            h.heat_score, h.industrial_score, h.vehicular_score, h.exposure_score, req.weights
        )
        if req.min_compound_score and new_score < req.min_compound_score:
            continue
        if req.severity_filter and new_sev != req.severity_filter.lower():
            continue
            
        evidence = dict(h.contributing_evidence)
        if req.weights:
            evidence["custom_weights_applied"] = req.weights.dict()
            
        items.append(CompoundHotspotItem(
            id=str(h.id),
            hotspot_code=h.hotspot_code,
            title=h.title,
            region_name=h.region.name if h.region else "Panvel and Navi Mumbai",
            heat_score=h.heat_score,
            industrial_score=h.industrial_score,
            vehicular_score=h.vehicular_score,
            exposure_score=h.exposure_score,
            compound_risk_score=new_score,
            severity=new_sev,
            primary_hazard=h.primary_hazard,
            area_sqkm=h.area_sqkm,
            detected_date=h.detected_date.isoformat(),
            methodology_version="ThermoSim-Dynamic-Custom-Weights",
            contributing_evidence=evidence,
            limitations=h.limitations,
            data_classification="modelled",
            geometry=geometry_to_geojson_dict(h.geom)
        ))
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="ThermoSim Dynamic Weight Engine", classification="modelled")
    )
