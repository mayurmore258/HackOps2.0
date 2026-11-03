"""
THERMOS AI - Geographic and Spatial Context Models
"""

from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.db.base import Base, UUIDMixin, TimestampMixin, SpatialGeometry


class Region(Base, UUIDMixin, TimestampMixin):
    """Broad geographic area of interest (e.g. Panvel, Navi Mumbai, Mumbai Metropolitan Region)."""
    __tablename__ = "regions"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    bounding_box = Column(JSON, nullable=True)  # [min_lon, min_lat, max_lon, max_lat]
    geom = Column(SpatialGeometry("POLYGON", srid=4326), nullable=True)
    area_sqkm = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    administrative_areas = relationship("AdministrativeArea", back_populates="region", cascade="all, delete-orphan")
    heat_hotspots = relationship("HeatHotspot", back_populates="region")
    compound_hotspots = relationship("CompoundHotspot", back_populates="region")


class AdministrativeArea(Base, UUIDMixin, TimestampMixin):
    """Sub-region boundary (ward, taluka, municipal corporation division)."""
    __tablename__ = "administrative_areas"

    region_id = Column(UUIDMixin.id.type, ForeignKey("regions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=True, index=True)
    admin_level = Column(String(50), default="ward", nullable=False)  # municipal_corporation, ward, taluka
    population = Column(Integer, nullable=True)
    area_sqkm = Column(Float, nullable=True)
    geom = Column(SpatialGeometry("MULTIPOLYGON", srid=4326), nullable=True)

    region = relationship("Region", back_populates="administrative_areas")
    exposure_assessments = relationship("CommunityExposureAssessment", back_populates="administrative_area")


class MonitoringLocation(Base, UUIDMixin, TimestampMixin):
    """In-situ environmental monitoring sensor or air quality monitoring station."""
    __tablename__ = "monitoring_locations"

    station_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    station_type = Column(String(50), default="caaqms", nullable=False)  # caaqms, imd, sensor_node, industrial
    operator = Column(String(100), default="CPCB / MPCB", nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_m = Column(Float, nullable=True)
    geom = Column(SpatialGeometry("POINT", srid=4326), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    observations = relationship("EnvironmentalObservation", back_populates="monitoring_location")
    pollutant_observations = relationship("PollutantObservation", back_populates="monitoring_location")


class IndustrialFacility(Base, UUIDMixin, TimestampMixin):
    """Registered industrial facility / manufacturing unit."""
    __tablename__ = "industrial_facilities"

    name = Column(String(200), nullable=False)
    industry_type = Column(String(100), nullable=False)  # Chemical, Petrochemical, Manufacturing, Textile, Power
    category = Column(String(20), default="Red", nullable=False)  # Red, Orange, Green, White (CPCB categorisation)
    consent_id = Column(String(100), nullable=True, index=True)
    district = Column(String(100), default="Raigad / Thane", nullable=False)
    state = Column(String(50), default="Maharashtra", nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(SpatialGeometry("POINT", srid=4326), nullable=True)
    address = Column(Text, nullable=True)
    is_cems_connected = Column(Boolean, default=False, nullable=False)

    industrial_hotspots = relationship("IndustrialHotspot", back_populates="facility")
    compliance_assessments = relationship("ComplianceAssessment", back_populates="facility")


class RoadSegment(Base, UUIDMixin, TimestampMixin):
    """Major road / transport corridor segment."""
    __tablename__ = "road_segments"

    osm_id = Column(String(50), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    road_type = Column(String(50), default="primary", nullable=False)  # motorway, trunk, primary, secondary
    length_m = Column(Float, nullable=True)
    lanes = Column(Integer, default=2, nullable=False)
    speed_limit_kmh = Column(Integer, default=50, nullable=True)
    geom = Column(SpatialGeometry("MULTILINESTRING", srid=4326), nullable=True)

    traffic_estimates = relationship("TrafficEmissionEstimate", back_populates="road_segment")
    vehicular_hotspots = relationship("VehicularHotspot", back_populates="road_segment")


class SensitiveLocation(Base, UUIDMixin, TimestampMixin):
    """High-vulnerability receptor (school, hospital, elder care, public park)."""
    __tablename__ = "sensitive_locations"

    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # hospital, school, elder_care, park, dense_residential
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(SpatialGeometry("POINT", srid=4326), nullable=True)
    address = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=True)


class PopulationGrid(Base, UUIDMixin, TimestampMixin):
    """Gridded population estimation cell (e.g. 500m or 1km grid)."""
    __tablename__ = "population_grids"

    cell_id = Column(String(50), nullable=False, index=True)
    geom = Column(SpatialGeometry("POLYGON", srid=4326), nullable=True)
    population_count = Column(Float, nullable=False)
    density_per_sqkm = Column(Float, nullable=False)
    year = Column(Integer, default=2021, nullable=False)
    source = Column(String(100), default="GHS-POP / WorldPop", nullable=False)

