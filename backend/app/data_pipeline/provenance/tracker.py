"""
THERMOS AI - Provenance and Data Lineage Tracker
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models.datasets import DataIngestionRun, Dataset

logger = get_logger(__name__)


class ProvenanceTracker:
    """Manages audit trails, checksums, and execution logs for data pipeline runs."""

    @staticmethod
    def record_run_start(
        db: Session,
        dataset_id: Any,
        file_path: Optional[str] = None
    ) -> DataIngestionRun:
        run = DataIngestionRun(
            dataset_id=dataset_id,
            run_timestamp=datetime.now(timezone.utc),
            status="running",
            records_ingested=0,
            file_path=file_path,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def record_run_completion(
        db: Session,
        run_id: Any,
        records_count: int,
        checksum: Optional[str] = None,
        duration_sec: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        run = db.query(DataIngestionRun).filter(DataIngestionRun.id == run_id).first()
        if run:
            run.status = "completed"
            run.records_ingested = records_count
            run.checksum = checksum
            run.execution_duration_sec = duration_sec
            run.provenance_metadata = metadata or {}
            db.commit()

    @staticmethod
    def record_run_failure(
        db: Session,
        run_id: Any,
        error_message: str
    ) -> None:
        run = db.query(DataIngestionRun).filter(DataIngestionRun.id == run_id).first()
        if run:
            run.status = "failed"
            run.error_message = error_message
            db.commit()

