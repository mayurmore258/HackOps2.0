"""
THERMOS AI - Environmental Datasets and Provenance API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.datasets import Dataset, DatasetSource, DataIngestionRun
from app.schemas.common import ResponseEnvelope, ResponseMetadata, PaginationMeta
from app.schemas.datasets import (
    DatasetResponse,
    DatasetSourceResponse,
    DataIngestionRunResponse,
)

router = APIRouter(prefix="/datasets", tags=["Datasets & Provenance"])


@router.get("", response_model=ResponseEnvelope[List[DatasetResponse]])
def list_datasets(
    classification: Optional[str] = Query(None, description="measured, satellite_derived, modelled, estimated, synthetic"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List registered environmental datasets with explicit data classifications and resolutions."""
    query = db.query(Dataset)
    if classification:
        query = query.filter(Dataset.data_classification == classification)
    total = query.count()
    datasets = query.order_by(Dataset.name).offset(offset).limit(limit).all()
    
    items = [
        DatasetResponse(
            id=str(d.id),
            code=d.code,
            name=d.name,
            description=d.description,
            data_classification=d.data_classification,
            spatial_resolution_m=d.spatial_resolution_m,
            temporal_resolution=d.temporal_resolution,
            unit=d.unit,
            crs=d.crs,
            coverage_area=d.coverage_area,
            limitations=d.limitations,
            is_active=d.is_active,
            source_name=d.source.name if d.source else None
        )
        for d in datasets
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(
            source="THERMOS AI Data Catalogue",
            classification="measured",
            pagination=PaginationMeta.create(total=total, limit=limit, offset=offset)
        )
    )


@router.get("/sources", response_model=ResponseEnvelope[List[DatasetSourceResponse]])
def list_dataset_sources(db: Session = Depends(get_db)):
    """List official external providers and research repositories."""
    sources = db.query(DatasetSource).all()
    items = [
        DatasetSourceResponse(
            id=str(s.id),
            code=s.code,
            name=s.name,
            provider=s.provider,
            website_url=s.website_url,
            license=s.license,
            update_frequency=s.update_frequency,
            citation=s.citation
        )
        for s in sources
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="Official Provenance Catalogue", classification="measured")
    )


@router.get("/runs", response_model=ResponseEnvelope[List[DataIngestionRunResponse]])
def list_ingestion_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List recent data pipeline ingestion audit executions and checksums."""
    runs = db.query(DataIngestionRun).order_by(DataIngestionRun.run_timestamp.desc()).limit(limit).all()
    items = [
        DataIngestionRunResponse(
            id=str(r.id),
            dataset_id=str(r.dataset_id),
            run_timestamp=r.run_timestamp.isoformat(),
            status=r.status,
            records_ingested=r.records_ingested,
            file_path=r.file_path,
            execution_duration_sec=r.execution_duration_sec,
            error_message=r.error_message
        )
        for r in runs
    ]
    return ResponseEnvelope(
        success=True,
        data=items,
        metadata=ResponseMetadata(source="Data Ingestion Audit Log", classification="measured")
    )
