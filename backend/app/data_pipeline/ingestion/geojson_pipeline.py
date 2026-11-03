"""
THERMOS AI - GeoJSON Vector Data Ingestion Pipeline
"""

from pathlib import Path
from typing import Any, Dict, List
import json
from shapely.geometry import shape

from app.data_pipeline.ingestion.base import BaseIngestionPipeline
from app.core.exceptions import DataIngestionError


class GeoJSONIngestionPipeline(BaseIngestionPipeline):
    """Pipeline for vector spatial layers (wards, administrative boundaries, road networks)."""

    def validate_file(self, file_path: Path) -> bool:
        if file_path.suffix.lower() not in [".geojson", ".json"]:
            return False
        return file_path.stat().st_size > 0

    def parse_and_transform(self, file_path: Path, **kwargs: Any) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            features = data.get("features", [])
            transformed = []
            
            for idx, feat in enumerate(features):
                geom = feat.get("geometry")
                props = feat.get("properties", {})
                
                # Validate geometry shape
                if geom:
                    _ = shape(geom)
                    
                record = {
                    "feature_id": feat.get("id", str(idx)),
                    "geometry": geom,
                    "properties": props
                }
                transformed.append(record)
                
            return transformed
        except Exception as e:
            raise DataIngestionError(f"Failed parsing GeoJSON {file_path}: {str(e)}")

