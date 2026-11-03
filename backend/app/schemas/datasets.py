"""
THERMOS AI - Datasets and Observation Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetSourceResponse(BaseModel):
    id: str
    code: str
    name: str
    provider: str
    website_url: Optional[str] = None
    license: str
    update_frequency: str
    citation: Optional[str] = None


class DatasetResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    data_classification: str
    spatial_resolution_m: Optional[float] = None
    temporal_resolution: str
    unit: Optional[str] = None
    crs: str
    coverage_area: str
    limitations: Optional[str] = None
    is_active: bool
    source_name: Optional[str] = None


class DataIngestionRunResponse(BaseModel):
    id: str
    dataset_id: str
    run_timestamp: str
    status: str
    records_ingested: int
    file_path: Optional[str] = None
    execution_duration_sec: Optional[float] = None
    error_message: Optional[str] = None

