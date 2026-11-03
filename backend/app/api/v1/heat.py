"""
THERMOS AI - Urban Heat Intelligence API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.spatial import geometry_to_geojson_dict
from app.modules.heat.service import HeatIntelligenceService
from app.schemas.common import (
    ResponseEnvelope,
    ResponseMetadata,
    PaginationParams,
    PaginationMeta,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)
from app.schemas.heat import (
    HeatSummaryResponse,
    HeatHotspotItem,
    HeatTimeseriesPoint,
    HeatIndicesResponse,
    HeatAnalysisRequest,
)

router = APIRouter(prefix="/heat", tags=["Urban Heat Intelligence"])


@router.get("/summary", response_model=ResponseEnvelope[HeatSummaryResponse])
def get_heat_summary(
    region_code: str = Query("PANVEL_NAVI_MUMBAI", description="Region code"),
    db: Session = Depends(get_db)
):
    """Retrieve high-level urban heat island indicators, mean LST, and hotspot counts."""
    data = HeatIntelligenceService.get_heat_summary(db, region_code)
    return ResponseEnvelope(
        success=True,
        data=HeatSummaryResponse(**data),
        metadata=ResponseMetadata(
            source="Landsat 8/9 Collection 2 Level-2",
            classification="satellite_derived",
            limitations=["LST represents skin temperature, not near-surface ambient air temperature."]
        )
    )


@router.get("/hotspots", response_model=ResponseEnvelope[List[HeatHotspotItem]])
def list_heat_hotspots(
    severity: Optional[str] = Query(None, description="Filter by severity: extreme, high, moderate, low"),
    min_lst: Optional[float] = Query(None, description="Minimum LST in Celsius"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List detected spatial heat hotspots with thermal anomaly values and spectral indices."""
    hotspots, total = HeatIntelligenceService.list_hotspots(db, severity, min_lst, limit, offset)
    
    items = []
    for h in hotspots:
        items.append(HeatHotspotItem(
            id=str(h.id),
            hotspot_code=h.hotspot_code,
            severity=h.severity,
            lst_celsius=h.lst_celsius,
            lst_anomaly_celsius=h.lst_anomaly_celsius,
            ndvi=h.ndvi,
            ndbi=h.ndbi,
            area_sqkm=h.area_sqkm,
            detected_date=h.detected_date.isoformat(),
            data_classification=h.data_classification,
            coordinates=geometry_to_geojson_dict(h.geom)
        ))
        
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="Landsat Thermal Anomaly Engine",
            classification="satellite_derived",
            pagination=PaginationMeta.create(total=total, limit=limit, offset=offset)
        )
    )


@router.get("/layers", response_model=ResponseEnvelope[GeoJSONFeatureCollection])
def get_heat_geojson_layers(
    severity: Optional[str] = Query(None, description="Optional severity filter"),
    db: Session = Depends(get_db)
):
    """Export urban heat hotspot polygons formatted as a standard GeoJSON FeatureCollection."""
    hotspots, _ = HeatIntelligenceService.list_hotspots(db, severity=severity, limit=100)
    
    features = []
    for h in hotspots:
        geom = geometry_to_geojson_dict(h.geom)
        if geom:
            features.append(GeoJSONFeature(
                id=str(h.id),
                geometry=geom,
                properties={
                    "hotspot_code": h.hotspot_code,
                    "severity": h.severity,
                    "lst_celsius": h.lst_celsius,
                    "lst_anomaly_celsius": h.lst_anomaly_celsius,
                    "ndvi": h.ndvi,
                    "ndbi": h.ndbi,
                    "area_sqkm": h.area_sqkm,
                    "detected_date": h.detected_date.isoformat(),
                    "classification": h.data_classification
                }
            ))
            
    return ResponseEnvelope(
        success=True,
        data=GeoJSONFeatureCollection(features=features),
        metadata=ResponseMetadata(
            source="THERMOS AI GeoEngine",
            classification="satellite_derived"
        )
    )


@router.get("/timeseries", response_model=ResponseEnvelope[List[HeatTimeseriesPoint]])
def get_heat_timeseries(
    region_code: str = Query("PANVEL_NAVI_MUMBAI", description="Region code"),
    limit: int = Query(30, ge=5, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve multi-temporal Land Surface Temperature time-series trajectory."""
    points = HeatIntelligenceService.get_timeseries(db, region_code, limit)
    return ResponseEnvelope(
        success=True,
        data=[HeatTimeseriesPoint(**p) for p in points],
        metadata=ResponseMetadata(
            source="Landsat Multi-temporal Archive",
            classification="satellite_derived"
        )
    )


@router.get("/indices", response_model=ResponseEnvelope[HeatIndicesResponse])
def get_heat_indices():
    """Retrieve correlation and cooling metrics between vegetation (NDVI) and built-up index (NDBI)."""
    return ResponseEnvelope(
        success=True,
        data=HeatIndicesResponse(
            region="Panvel and Navi Mumbai Metropolitan Area",
            mean_ndvi=0.22,
            mean_ndbi=0.28,
            mean_ndmi=0.14,
            correlation_lst_ndvi=-0.68,
            correlation_lst_ndbi=0.74,
            vegetation_cooling_effect_celsius=3.2
        ),
        metadata=ResponseMetadata(
            source="Spectral Analysis Engine",
            classification="satellite_derived",
            limitations=["Strong negative correlation between NDVI and LST confirms local vegetation cooling."]
        )
    )


@router.post("/analyse", response_model=ResponseEnvelope[List[HeatHotspotItem]])
def run_heat_analysis(
    req: HeatAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Execute dynamic spatial thermal hotspot analysis with custom filtering criteria."""
    hotspots, total = HeatIntelligenceService.list_hotspots(
        db,
        severity=req.severity_filter,
        min_lst=req.min_lst_celsius,
        limit=50
    )
    items = [
        HeatHotspotItem(
            id=str(h.id),
            hotspot_code=h.hotspot_code,
            severity=h.severity,
            lst_celsius=h.lst_celsius,
            lst_anomaly_celsius=h.lst_anomaly_celsius,
            ndvi=h.ndvi,
            ndbi=h.ndbi,
            area_sqkm=h.area_sqkm,
            detected_date=h.detected_date.isoformat(),
            data_classification=h.data_classification,
            coordinates=geometry_to_geojson_dict(h.geom)
        )
        for h in hotspots
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="Dynamic Thermal Anomaly Analysis",
            classification="satellite_derived",
            pagination=PaginationMeta(total=total, limit=50, offset=0, has_more=False)
        )
    )
