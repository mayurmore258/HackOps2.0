"""
THERMOS AI - Dataset Provenance and Environmental Observations Models
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.db.base import Base, UUIDMixin, TimestampMixin, SpatialGeometry


class DatasetSource(Base, UUIDMixin, TimestampMixin):
    """Catalog of official data providers and research sources."""
    __tablename__ = "dataset_sources"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    provider = Column(String(150), nullable=False)  # USGS, ESA, CPCB, MPCB, CHETNA-Road, GEE
    website_url = Column(String(255), nullable=True)
    license = Column(String(100), default="Open Access", nullable=False)
    update_frequency = Column(String(50), default="daily", nullable=False)
    citation = Column(Text, nullable=True)

    datasets = relationship("Dataset", back_populates="source")


class Dataset(Base, UUIDMixin, TimestampMixin):
    """Specific environmental dataset catalogue entry with full provenance metadata."""
    __tablename__ = "datasets"

    source_id = Column(UUIDMixin.id.type, ForeignKey("dataset_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    
    # Scientific data classification (strictly enforced)
    # measured, satellite_derived, reanalysis, modelled, estimated, simulated, synthetic, unavailable
    data_classification = Column(String(30), default="satellite_derived", nullable=False, index=True)
    spatial_resolution_m = Column(Float, nullable=True)
    temporal_resolution = Column(String(50), default="daily", nullable=False)
    unit = Column(String(50), nullable=True)
    crs = Column(String(50), default="EPSG:4326", nullable=False)
    coverage_area = Column(String(100), default="Mumbai Metropolitan Region", nullable=False)
    limitations = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    source = relationship("DatasetSource", back_populates="datasets")
    ingestion_runs = relationship("DataIngestionRun", back_populates="dataset")
    observations = relationship("EnvironmentalObservation", back_populates="dataset")


class DataIngestionRun(Base, UUIDMixin, TimestampMixin):
    """Audit log of pipeline ingestion executions."""
    __tablename__ = "data_ingestion_runs"

    dataset_id = Column(UUIDMixin.id.type, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    run_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(30), default="completed", nullable=False)  # pending, running, completed, failed
    records_ingested = Column(Integer, default=0, nullable=False)
    file_path = Column(String(255), nullable=True)
    checksum = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    execution_duration_sec = Column(Float, nullable=True)
    provenance_metadata = Column(JSON, nullable=True)

    dataset = relationship("Dataset", back_populates="ingestion_runs")


class EnvironmentalObservation(Base, UUIDMixin, TimestampMixin):
    """Generic normalized observation from monitoring stations or sensors."""
    __tablename__ = "environmental_observations"

    dataset_id = Column(UUIDMixin.id.type, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    monitoring_location_id = Column(UUIDMixin.id.type, ForeignKey("monitoring_locations.id", ondelete="SET NULL"), nullable=True, index=True)
    variable_name = Column(String(50), nullable=False, index=True)  # PM2.5, PM10, LST, SO2, NO2
    value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    geom = Column(SpatialGeometry("POINT", srid=4326), nullable=True)
    quality_flag = Column(String(30), default="validated", nullable=False)
    data_classification = Column(String(30), default="measured", nullable=False)

    dataset = relationship("Dataset", back_populates="observations")
    monitoring_location = relationship("MonitoringLocation", back_populates="observations")


class HeatObservation(Base, UUIDMixin, TimestampMixin):
    """Thermal remote sensing summary observations (Landsat/MODIS/Sentinel-2)."""
    __tablename__ = "heat_observations"

    region_id = Column(UUIDMixin.id.type, ForeignKey("regions.id", ondelete="CASCADE"), nullable=False, index=True)
    acquisition_date = Column(DateTime(timezone=True), nullable=False, index=True)
    sensor = Column(String(50), default="Landsat 8/9 Level-2", nullable=False)
    mean_lst_celsius = Column(Float, nullable=False)
    min_lst_celsius = Column(Float, nullable=False)
    max_lst_celsius = Column(Float, nullable=False)
    mean_ndvi = Column(Float, nullable=True)
    mean_ndbi = Column(Float, nullable=True)
    mean_ndmi = Column(Float, nullable=True)
    cloud_cover_percent = Column(Float, default=0.0, nullable=False)
    raster_asset_uri = Column(String(255), nullable=True)
    geom = Column(SpatialGeometry("POLYGON", srid=4326), nullable=True)
    data_classification = Column(String(30), default="satellite_derived", nullable=False)
    limitations = Column(Text, default="LST represents skin temperature, not near-surface ambient air temperature.", nullable=False)


class PollutantObservation(Base, UUIDMixin, TimestampMixin):
    """Atmospheric pollutant columns or ambient station concentration observations."""
    __tablename__ = "pollutant_observations"

    monitoring_location_id = Column(UUIDMixin.id.type, ForeignKey("monitoring_locations.id", ondelete="SET NULL"), nullable=True, index=True)
    industrial_facility_id = Column(UUIDMixin.id.type, ForeignKey("industrial_facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    pollutant = Column(String(20), nullable=False, index=True)  # SO2, NO2, PM2.5, PM10, CO, O3
    concentration_value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)  # ug/m3, mol/m2, ppb
    averaging_period = Column(String(20), default="24h", nullable=False)  # 1h, 8h, 24h, annual
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    wind_speed_ms = Column(Float, nullable=True)
    wind_direction_deg = Column(Float, nullable=True)
    geom = Column(SpatialGeometry("POINT", srid=4326), nullable=True)
    data_classification = Column(String(30), default="measured", nullable=False)  # measured or satellite_derived

    monitoring_location = relationship("MonitoringLocation", back_populates="pollutant_observations")


class TrafficEmissionEstimate(Base, UUIDMixin, TimestampMixin):
    """High-resolution gridded road transport emission estimates (CHETNA-Road)."""
    __tablename__ = "traffic_emission_estimates"

    road_segment_id = Column(UUIDMixin.id.type, ForeignKey("road_segments.id", ondelete="SET NULL"), nullable=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    co2_kg_per_km_day = Column(Float, nullable=False)
    nox_g_per_km_day = Column(Float, nullable=False)
    pm_g_per_km_day = Column(Float, nullable=False)
    co_g_per_km_day = Column(Float, nullable=False)
    model_source = Column(String(100), default="CHETNA-Road (Mittakola et al. 2025)", nullable=False)
    grid_resolution_m = Column(Float, default=500.0, nullable=False)
    geom = Column(SpatialGeometry("POLYGON", srid=4326), nullable=True)
    data_classification = Column(String(30), default="modelled", nullable=False)
    limitations = Column(Text, default="Modelled historical 2021 road-emission data; not live real-time traffic sensor readings.", nullable=False)

    road_segment = relationship("RoadSegment", back_populates="traffic_estimates")

