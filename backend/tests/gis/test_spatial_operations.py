"""
GIS and Spatial Operation Tests
"""

import pytest
from app.db.spatial import (
    haversine_distance_km,
    point_from_coordinates,
    calculate_area_sqm,
    point_in_polygon,
    buffer_point_meters,
)


def test_haversine_distance():
    """Verify great-circle distance calculation between Panvel and Vashi."""
    # Panvel: ~18.9894 N, 73.1175 E
    # Vashi: ~19.0770 N, 72.9986 E
    dist_km = haversine_distance_km(73.1175, 18.9894, 72.9986, 19.0770)
    # Expected distance: ~15 to 17 km
    assert 14.0 <= dist_km <= 18.0


def test_point_from_coordinates():
    """Verify GeoJSON point formatting and coordinate range validation."""
    pt = point_from_coordinates(73.1175, 18.9894)
    assert pt["type"] == "Point"
    assert pt["coordinates"] == [73.1175, 18.9894]
    
    with pytest.raises(Exception):
        point_from_coordinates(195.0, 18.0)  # Invalid longitude


def test_point_in_polygon():
    """Verify point-in-polygon containment check."""
    poly = {
        "type": "Polygon",
        "coordinates": [[
            [73.10, 18.95],
            [73.20, 18.95],
            [73.20, 19.05],
            [73.10, 19.05],
            [73.10, 18.95]
        ]]
    }
    # Inside point
    assert point_in_polygon(73.15, 19.00, poly) is True
    # Outside point
    assert point_in_polygon(73.25, 19.00, poly) is False


def test_metric_area_calculation():
    """Verify metric area calculation using projected UTM Zone 43N."""
    # Approximate 1 km x 1 km polygon (0.009 deg approx 1 km)
    poly = {
        "type": "Polygon",
        "coordinates": [[
            [73.100, 19.000],
            [73.109, 19.000],
            [73.109, 19.009],
            [73.100, 19.009],
            [73.100, 19.000]
        ]]
    }
    area_sqm = calculate_area_sqm(poly)
    # 1 km^2 = 1,000,000 m^2 (allow reasonable reprojection tolerance ~800,000 to 1,200,000)
    assert 700000.0 <= area_sqm <= 1300000.0


def test_buffer_point_meters():
    """Verify metric buffer polygon generation around a center point."""
    buf = buffer_point_meters(73.1175, 18.9894, distance_meters=500.0)
    assert buf["type"] == "Polygon"
    assert len(buf["coordinates"][0]) >= 4

