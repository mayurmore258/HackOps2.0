"""
THERMOS AI - CSV Environmental Data Ingestion Pipeline
"""

from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

from app.data_pipeline.ingestion.base import BaseIngestionPipeline
from app.core.exceptions import DataIngestionError


class CSVIngestionPipeline(BaseIngestionPipeline):
    """Pipeline for tabular environmental monitoring data (e.g. CPCB/CAAQMS CSV logs)."""

    def validate_file(self, file_path: Path) -> bool:
        if not file_path.suffix.lower() == ".csv":
            return False
        return file_path.stat().st_size > 0

    def parse_and_transform(self, file_path: Path, **kwargs: Any) -> List[Dict[str, Any]]:
        try:
            df = pd.read_csv(file_path)
            # Normalize column names to lowercase snake_case
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            
            records = []
            for _, row in df.iterrows():
                rec = row.to_dict()
                # Clean NaNs
                clean_rec = {k: (None if pd.isna(v) else v) for k, v in rec.items()}
                records.append(clean_rec)
                
            return records
        except Exception as e:
            raise DataIngestionError(f"Failed parsing CSV {file_path}: {str(e)}")

