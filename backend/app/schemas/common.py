"""
THERMOS AI - Common Pydantic Schemas, Response Envelopes, and GeoJSON Types
"""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    limit: int = Field(default=50, ge=1, le=1000, description="Items per page")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class PaginationMeta(BaseModel):
    """Metadata about paginated results."""
    total: int
    limit: int
    offset: int
    has_more: bool

    @classmethod
    def create(cls, total: int, limit: Any = 50, offset: Any = 0) -> "PaginationMeta":
        """Safely create PaginationMeta handling FastAPI Query defaults."""
        lim = int(getattr(limit, "default", limit) if getattr(limit, "default", None) is not None else limit or 50)
        off = int(getattr(offset, "default", offset) if getattr(offset, "default", None) is not None else offset or 0)
        return cls(total=total, limit=lim, offset=off, has_more=(off + lim) < total)


class ResponseMetadata(BaseModel):
    """Standard metadata attached to every API response."""
    source: Optional[str] = Field(default="THERMOS AI Intelligence Engine", description="Source of the data")
    classification: str = Field(
        default="modelled",
        description="Data classification: measured | satellite_derived | reanalysis | modelled | estimated | simulated | synthetic | unavailable"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of response generation"
    )
    pagination: Optional[PaginationMeta] = None
    limitations: Optional[List[str]] = Field(default=None, description="Scientific limitations or disclaimers")


class ErrorDetail(BaseModel):
    """Structured error object inside API responses."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard API response structure across all THERMOS AI endpoints."""
    success: bool = True
    data: Optional[T] = None
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)
    error: Optional[ErrorDetail] = None


# --- GeoJSON Schemas (RFC 7946) ---

class GeoJSONGeometry(BaseModel):
    """Standard GeoJSON geometry object."""
    type: str = Field(..., description="Point, Polygon, MultiPolygon, LineString, MultiLineString")
    coordinates: Any = Field(..., description="GeoJSON coordinates array [lon, lat] or nested")


class GeoJSONFeature(BaseModel):
    """Standard GeoJSON Feature object."""
    type: str = "Feature"
    id: Optional[str] = None
    geometry: Optional[GeoJSONGeometry] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class GeoJSONFeatureCollection(BaseModel):
    """Standard GeoJSON FeatureCollection object."""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature] = Field(default_factory=list)
