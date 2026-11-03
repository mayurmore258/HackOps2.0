"""
THERMOS AI - NetCDF Environmental Data Pipeline (CHETNA-Road / Climate Grids)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import xarray as xr
import numpy as np

from app.data_pipeline.ingestion.base import BaseIngestionPipeline
from app.core.exceptions import DataIngestionError


class NetCDFIngestionPipeline(BaseIngestionPipeline):
    """
    Ingestion pipeline for NetCDF gridded datasets such as CHETNA-Road
    (High-resolution Gridded CO2 and Pollutant Emission Data from Road Traffic in Indian Cities).
    """

    def validate_file(self, file_path: Path) -> bool:
        if file_path.suffix.lower() not in [".nc", ".nc4", ".netcdf"]:
            return False
        return file_path.stat().st_size > 0

    def parse_and_transform(
        self,
        file_path: Path,
        bounding_box: Optional[List[float]] = None,
        variables: Optional[List[str]] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Extract gridded emission slices within a target bounding box [min_lon, min_lat, max_lon, max_lat].
        Preserves spatial grid resolution and metadata.
        """
        try:
            ds = xr.open_dataset(file_path)
            vars_to_extract = variables or [v for v in ds.data_vars]
            
            # Identify spatial dimension coordinate names (lon/lat or x/y)
            lon_dim = "lon" if "lon" in ds.coords else ("longitude" if "longitude" in ds.coords else None)
            lat_dim = "lat" if "lat" in ds.coords else ("latitude" if "latitude" in ds.coords else None)
            
            if not lon_dim or not lat_dim:
                # Return dataset summary if dimensions are not standard
                return [{
                    "type": "netcdf_summary",
                    "variables": list(ds.data_vars),
                    "dimensions": dict(ds.sizes),
                    "attributes": dict(ds.attrs)
                }]
                
            # Filter bounding box if specified
            if bounding_box and len(bounding_box) == 4:
                min_lon, min_lat, max_lon, max_lat = bounding_box
                ds = ds.sel(
                    {
                        lon_dim: slice(min_lon, max_lon),
                        lat_dim: slice(min_lat, max_lat)
                    }
                )
                
            records = []
            lons = ds[lon_dim].values
            lats = ds[lat_dim].values
            
            # Sample or iterate grid cells (limit to max 5000 cells to prevent memory bloat)
            for i, lat in enumerate(lats[:100]):
                for j, lon in enumerate(lons[:100]):
                    cell_data = {
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "grid_resolution_deg": float(abs(lons[1] - lons[0])) if len(lons) > 1 else 0.005,
                        "values": {}
                    }
                    for v in vars_to_extract:
                        val = ds[v].values
                        if val.ndim == 2:
                            cell_data["values"][v] = float(val[i, j]) if not np.isnan(val[i, j]) else 0.0
                        elif val.ndim == 3:
                            cell_data["values"][v] = float(val[0, i, j]) if not np.isnan(val[0, i, j]) else 0.0
                    records.append(cell_data)
                    
            ds.close()
            return records
        except Exception as e:
            raise DataIngestionError(f"Failed parsing NetCDF {file_path}: {str(e)}")

