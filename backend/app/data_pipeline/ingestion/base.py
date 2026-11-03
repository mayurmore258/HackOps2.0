"""
THERMOS AI - Data Pipeline Base Ingestion Interface
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib

from app.core.logging import get_logger
from app.core.exceptions import DataIngestionError

logger = get_logger(__name__)


class BaseIngestionPipeline(ABC):
    """Abstract base class for all environmental data ingestion pipelines."""

    def __init__(self, dataset_code: str, source_code: str):
        self.dataset_code = dataset_code
        self.source_code = source_code
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def validate_file(self, file_path: Path) -> bool:
        """Validate file existence, extension, and integrity."""
        pass

    @abstractmethod
    def parse_and_transform(self, file_path: Path, **kwargs: Any) -> List[Dict[str, Any]]:
        """Parse raw file contents into standardized record dictionaries."""
        pass

    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of raw source file for provenance audit."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def run(self, file_path: Path, db_session: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute complete ingestion pipeline: validate -> checksum -> parse -> persist."""
        start_time = datetime.now(timezone.utc)
        self.logger.info("Starting data ingestion", dataset_code=self.dataset_code, file=str(file_path))
        
        if not file_path.exists():
            raise DataIngestionError(f"Source file not found: {file_path}")
            
        if not self.validate_file(file_path):
            raise DataIngestionError(f"Validation failed for source file: {file_path}")
            
        checksum = self.calculate_checksum(file_path)
        records = self.parse_and_transform(file_path, **kwargs)
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        self.logger.info(
            "Ingestion parsing completed",
            dataset_code=self.dataset_code,
            records_count=len(records),
            duration_sec=duration
        )
        
        return {
            "dataset_code": self.dataset_code,
            "records_parsed": len(records),
            "checksum": checksum,
            "duration_seconds": duration,
            "records": records
        }

