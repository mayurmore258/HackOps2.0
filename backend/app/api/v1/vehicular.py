"""
THERMOS AI - Vehicular Emission Intelligence API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.spatial import geometry_to_geojson_dict
from app.modules.vehicular.service import VehicularIntelligenceService
from app.schemas.common import (
    ResponseEnvelope,
    ResponseMetadata,
    PaginationMeta,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)
from app.schemas.vehicular import (
    VehicularSummaryResponse,
    RoadSegmentResponse,
    VehicularHotspotItem,
    VehicularTimeseriesPoint,
)

router = APIRouter(prefix="/vehicular", tags=["Vehicular Emission Intelligence"])


@router.get("/summary", response_model=ResponseEnvelope[VehicularSummaryResponse])
def get_vehicular_summary(
    region_code: str = Query("PANVEL_NAVI_MUMBAI", description="Region code"),
    db: Session = Depends(get_db)
):
    """Retrieve gridded road transport emission summaries, NOx and CO2 averages from CHETNA-Road."""
    data = VehicularIntelligenceService.get_vehicular_summary(db, region_code)
    return ResponseEnvelope(
        success=True,
        data=VehicularSummaryResponse(**data),
        metadata=ResponseMetadata(
            source="CHETNA-Road (Mittakola et al. 2025)",
            classification="modelled",
            limitations=["Historical 2021 gridded road-emission model; not real-time roadside concentration."]
        )
    )


@router.get("/roads", response_model=ResponseEnvelope[List[RoadSegmentResponse]])
def list_road_segments(
    road_type: Optional[str] = Query(None, description="motorway, trunk, primary, secondary"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List monitored highway and transport segments with estimated NOx/CO2 intensity."""
    roads, total = VehicularIntelligenceService.list_roads(db, road_type, limit, offset)
    items = []
    for r in roads:
        latest_est = r.traffic_estimates[-1] if r.traffic_estimates else None
        items.append(RoadSegmentResponse(
            id=str(r.id),
            osm_id=r.osm_id,
            name=r.name,
            road_type=r.road_type,
            length_m=r.length_m,
            lanes=r.lanes,
            speed_limit_kmh=r.speed_limit_kmh,
            latest_nox_g_km_day=latest_est.nox_g_per_km_day if latest_est else 175.0,
            latest_co2_kg_km_day=latest_est.co2_kg_per_km_day if latest_est else 315.0
        ))
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="OpenStreetMap & CHETNA-Road",
            classification="modelled",
            pagination=PaginationMeta.create(total=total, limit=limit, offset=offset)
        )
    )


@router.get("/hotspots", response_model=ResponseEnvelope[List[VehicularHotspotItem]])
def list_vehicular_hotspots(
    severity: Optional[str] = Query(None, description="high, moderate, low"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List heavy-emission freight and commuter corridors."""
    hotspots, total = VehicularIntelligenceService.list_hotspots(db, severity, limit, offset)
    items = [
        VehicularHotspotItem(
            id=str(h.id),
            hotspot_code=h.hotspot_code,
            road_name=h.road_segment.name if h.road_segment else None,
            road_segment_id=str(h.road_segment_id) if h.road_segment_id else None,
            pollutant=h.pollutant,
            emission_intensity=h.emission_intensity,
            unit=h.unit,
            severity=h.severity,
            detected_date=h.detected_date.isoformat(),
            traffic_context=h.traffic_context,
            data_classification=h.data_classification
        )
        for h in hotspots
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="CHETNA-Road Corridor Analytics",
            classification="modelled",
            pagination=PaginationMeta.create(total=total, limit=limit, offset=offset)
        )
    )


@router.get("/timeseries", response_model=ResponseEnvelope[List[VehicularTimeseriesPoint]])
def get_vehicular_timeseries(
    limit: int = Query(30, ge=5, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve road transport emission timeseries along priority corridors."""
    pts = VehicularIntelligenceService.get_timeseries(db, limit)
    return ResponseEnvelope(
        success=True,
        data=[VehicularTimeseriesPoint(**p) for p in pts],
        metadata=ResponseMetadata(
            source="CHETNA-Road Daily Temporal Archive",
            classification="modelled"
        )
    )


@router.get("/layers", response_model=ResponseEnvelope[GeoJSONFeatureCollection])
def get_vehicular_geojson_layers(
    db: Session = Depends(get_db)
):
    """Export road network emission intensity segments as GeoJSON FeatureCollection."""
    roads, _ = VehicularIntelligenceService.list_roads(db, limit=100)
    features = []
    for r in roads:
        geom = geometry_to_geojson_dict(r.geom)
        if geom:
            latest_est = r.traffic_estimates[-1] if r.traffic_estimates else None
            features.append(GeoJSONFeature(
                id=str(r.id),
                geometry=geom,
                properties={
                    "name": r.name,
                    "road_type": r.road_type,
                    "lanes": r.lanes,
                    "nox_g_km_day": latest_est.nox_g_per_km_day if latest_est else 175.0,
                    "co2_kg_km_day": latest_est.co2_kg_per_km_day if latest_est else 315.0,
                    "classification": "modelled"
                }
            ))
    return ResponseEnvelope(
        success=True,
        data=GeoJSONFeatureCollection(features=features),
        metadata=ResponseMetadata(source="THERMOS AI GeoEngine", classification="modelled")
    )


@router.post("/analyse", response_model=ResponseEnvelope[List[VehicularHotspotItem]])
def run_vehicular_analysis(
    db: Session = Depends(get_db)
):
    """Run dynamic corridor ranking and traffic emission hotspot screening."""
    hotspots, total = VehicularIntelligenceService.list_hotspots(db, limit=50)
    items = [
        VehicularHotspotItem(
            id=str(h.id),
            hotspot_code=h.hotspot_code,
            road_name=h.road_segment.name if h.road_segment else None,
            road_segment_id=str(h.road_segment_id) if h.road_segment_id else None,
            pollutant=h.pollutant,
            emission_intensity=h.emission_intensity,
            unit=h.unit,
            severity=h.severity,
            detected_date=h.detected_date.isoformat(),
            traffic_context=h.traffic_context,
            data_classification=h.data_classification
        )
        for h in hotspots
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="CHETNA-Road Multi-corridor Analysis", classification="modelled")
    )
