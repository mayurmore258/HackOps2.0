"""
THERMOS AI - Spatial Database Types and GIS Utilities

Provides database-agnostic spatial support:
- Native PostGIS Geometry on PostgreSQL
- Transparent WKT/GeoJSON serialization on SQLite
- Metric spatial computations (UTM Zone 43N / EPSG:32643)
- Distance, area, buffer, and point-in-polygon operations
"""

import json
import math
from typing import Any, Dict, Optional, Tuple, Union

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import shape, mapping, Point, Polygon, MultiPolygon
from shapely import from_wkt, to_wkt, from_geojson, to_geojson
import pyproj
from shapely.ops import transform

from app.core.config import settings
from app.core.exceptions import SpatialOperationError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Transformers for metric calculations (WGS84 -> UTM Zone 43N for Western India)
_WGS84 = pyproj.CRS("EPSG:4326")
_UTM43N = pyproj.CRS(f"EPSG:{settings.PROJECTED_SRID}")
_PROJECT_TO_UTM = pyproj.Transformer.from_crs(_WGS84, _UTM43N, always_xy=True).transform
_PROJECT_TO_WGS84 = pyproj.Transformer.from_crs(_UTM43N, _WGS84, always_xy=True).transform


class SpatialGeometry(TypeDecorator):
    """
    Polymorphic spatial geometry column.
    
    Uses native PostGIS `Geometry` when running on PostgreSQL,
    and falls back cleanly to `Text` (storing WKT or GeoJSON) on SQLite.
    """
    impl = Text
    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326, **kwargs: Any):
        self.geometry_type = geometry_type.upper()
        self.srid = srid
        super().__init__(**kwargs)

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Geometry(geometry_type=self.geometry_type, srid=self.srid))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
            
        if dialect.name == "postgresql":
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                s = shape(value)
                return from_shape(s, srid=self.srid)
            if hasattr(value, "geom_type"):
                return from_shape(value, srid=self.srid)
            return value
        else:
            # SQLite fallback: serialize to GeoJSON or WKT string
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                return json.dumps(value)
            if hasattr(value, "geom_type"):
                return to_wkt(value)
            return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
            
        if dialect.name == "postgresql":
            try:
                geom = to_shape(value)
                return mapping(geom)
            except Exception:
                return value
        else:
            # SQLite fallback
            if isinstance(value, str):
                val_trimmed = value.strip()
                if val_trimmed.startswith("{"):
                    try:
                        return json.loads(val_trimmed)
                    except Exception:
                        pass
                try:
                    s = from_wkt(val_trimmed)
                    return mapping(s)
                except Exception:
                    return val_trimmed
            return value


# --- GIS Spatial Utility Functions ---

def geometry_to_geojson_dict(geom_input: Any) -> Optional[Dict[str, Any]]:
    """Convert any supported geometry format to GeoJSON geometry dictionary."""
    if geom_input is None:
        return None
    if isinstance(geom_input, dict):
        if "type" in geom_input and "coordinates" in geom_input:
            return geom_input
        if "geometry" in geom_input:
            return geom_input["geometry"]
    if isinstance(geom_input, str):
        trimmed = geom_input.strip()
        if trimmed.startswith("{"):
            parsed = json.loads(trimmed)
            if "coordinates" in parsed:
                return parsed
        s = from_wkt(trimmed)
        return mapping(s)
    if hasattr(geom_input, "geom_type"):
        return mapping(geom_input)
    try:
        s = to_shape(geom_input)
        return mapping(s)
    except Exception as e:
        raise SpatialOperationError(f"Cannot convert to GeoJSON: {str(e)}")


def geometry_from_geojson_dict(data: Dict[str, Any]) -> Any:
    """Convert GeoJSON geometry dict to Shapely shape."""
    try:
        return shape(data)
    except Exception as e:
        raise SpatialOperationError(f"Invalid GeoJSON shape: {str(e)}")


def point_from_coordinates(lon: float, lat: float) -> Dict[str, Any]:
    """Create a GeoJSON Point dictionary from [lon, lat] coordinates."""
    if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
        raise SpatialOperationError(f"Invalid coordinates: lon={lon}, lat={lat}")
    return {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]}


def haversine_distance_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate great-circle distance between two points in kilometers."""
    r = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def calculate_area_sqm(geom_geojson: Dict[str, Any]) -> float:
    """Calculate area of geometry in square meters using projected UTM Zone 43N."""
    try:
        s_wgs84 = shape(geom_geojson)
        s_utm = transform(_PROJECT_TO_UTM, s_wgs84)
        return float(s_utm.area)
    except Exception as e:
        raise SpatialOperationError(f"Area calculation failed: {str(e)}")


def buffer_point_meters(lon: float, lat: float, distance_meters: float) -> Dict[str, Any]:
    """Create a metric buffer polygon around a lon/lat point, returned in EPSG:4326."""
    try:
        pt_wgs84 = Point(lon, lat)
        pt_utm = transform(_PROJECT_TO_UTM, pt_wgs84)
        buf_utm = pt_utm.buffer(distance_meters)
        buf_wgs84 = transform(_PROJECT_TO_WGS84, buf_utm)
        return mapping(buf_wgs84)
    except Exception as e:
        raise SpatialOperationError(f"Buffer calculation failed: {str(e)}")


def point_in_polygon(lon: float, lat: float, polygon_geojson: Dict[str, Any]) -> bool:
    """Check if a lon/lat point lies inside a polygon geometry."""
    try:
        pt = Point(lon, lat)
        poly = shape(polygon_geojson)
        return bool(poly.contains(pt))
    except Exception as e:
        raise SpatialOperationError(f"Point-in-polygon check failed: {str(e)}")

