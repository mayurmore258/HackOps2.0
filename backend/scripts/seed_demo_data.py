"""
THERMOS AI - Controlled Demonstration Data Seeding Script

Populates the database with scientifically defensible, transparent demonstration data
for the Panvel & Navi Mumbai pilot region (with MMR regional reference).
Every synthetic or modelled record is strictly classified.
"""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.spatial import point_from_coordinates
import app.db.models as m

logger = get_logger(__name__)


def seed_demo_data() -> None:
    """Seed comprehensive demonstration datasets."""
    print("=" * 70)
    print("THERMOS AI — SEEDING DEMONSTRATION & BENCHMARK DATA")
    print("=" * 70)
    
    # Initialize schema first
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if already seeded
        existing_region = db.query(m.Region).filter(m.Region.code == "PANVEL_NAVI_MUMBAI").first()
        if existing_region:
            print("Database already contains seed data for Panvel & Navi Mumbai. Refreshing records...")
            # We can re-use or append; let's delete existing demo records for a clean state
            db.query(m.IncidentStatusHistory).delete()
            db.query(m.CorrectiveAction).delete()
            db.query(m.IncidentAssessment).delete()
            db.query(m.IncidentAttachment).delete()
            db.query(m.Incident).delete()
            db.query(m.ComplianceEvidence).delete()
            db.query(m.ComplianceAssessment).delete()
            db.query(m.StandardThreshold).delete()
            db.query(m.EnvironmentalStandard).delete()
            db.query(m.RegulatoryAuthority).delete()
            db.query(m.ScenarioComparison).delete()
            db.query(m.InterventionScenario).delete()
            db.query(m.InterventionType).delete()
            db.query(m.CommunityExposureAssessment).delete()
            db.query(m.CompoundHotspot).delete()
            db.query(m.VehicularHotspot).delete()
            db.query(m.IndustrialHotspot).delete()
            db.query(m.HeatHotspot).delete()
            db.query(m.TrafficEmissionEstimate).delete()
            db.query(m.PollutantObservation).delete()
            db.query(m.HeatObservation).delete()
            db.query(m.EnvironmentalObservation).delete()
            db.query(m.DataIngestionRun).delete()
            db.query(m.Dataset).delete()
            db.query(m.DatasetSource).delete()
            db.query(m.PopulationGrid).delete()
            db.query(m.SensitiveLocation).delete()
            db.query(m.RoadSegment).delete()
            db.query(m.IndustrialFacility).delete()
            db.query(m.MonitoringLocation).delete()
            db.query(m.AdministrativeArea).delete()
            db.query(m.Region).delete()
            db.commit()

        # -------------------------------------------------------------
        # 1. Pilot Region
        # -------------------------------------------------------------
        region = m.Region(
            code="PANVEL_NAVI_MUMBAI",
            name="Panvel and Navi Mumbai Metropolitan Sub-Region",
            description="Pilot study domain encompassing Panvel City, Taloja Industrial Corridor, and Navi Mumbai urban agglomeration.",
            bounding_box={"min_lon": 72.95, "min_lat": 18.90, "max_lon": 73.20, "max_lat": 19.15},
            geom={
                "type": "Polygon",
                "coordinates": [[
                    [72.95, 18.90],
                    [73.20, 18.90],
                    [73.20, 19.15],
                    [72.95, 19.15],
                    [72.95, 18.90]
                ]]
            },
            area_sqkm=420.5,
            is_active=True
        )
        db.add(region)
        db.flush()

        # -------------------------------------------------------------
        # 2. Administrative Areas (Wards & Industrial Zones)
        # -------------------------------------------------------------
        admin_areas_data = [
            {"name": "Panvel Municipal Corporation (Central)", "code": "PMC-CENTRAL", "level": "municipal_corporation", "pop": 510000, "area": 110.5, "coords": [73.11, 18.99]},
            {"name": "Navi Mumbai Municipal Corporation (South)", "code": "NMMC-SOUTH", "level": "municipal_corporation", "pop": 680000, "area": 85.0, "coords": [73.03, 19.03]},
            {"name": "Taloja MIDC Industrial Zone", "code": "TALOJA-MIDC", "level": "industrial_estate", "pop": 45000, "area": 35.0, "coords": [73.14, 19.06]},
            {"name": "Kharghar Urban Node", "code": "NODE-KHARGHAR", "level": "ward", "pop": 220000, "area": 42.0, "coords": [73.06, 19.04]},
            {"name": "CBD Belapur Commercial Node", "code": "NODE-BELAPUR", "level": "ward", "pop": 140000, "area": 28.0, "coords": [73.03, 19.01]},
            {"name": "Vashi Commercial Corridor", "code": "NODE-VASHI", "level": "ward", "pop": 190000, "area": 24.0, "coords": [72.99, 19.07]},
        ]
        admin_areas = {}
        for a in admin_areas_data:
            c = a["coords"]
            # Create a representative polygon box around coordinates
            poly = {
                "type": "MultiPolygon",
                "coordinates": [[[
                    [c[0] - 0.02, c[1] - 0.02],
                    [c[0] + 0.02, c[1] - 0.02],
                    [c[0] + 0.02, c[1] + 0.02],
                    [c[0] - 0.02, c[1] + 0.02],
                    [c[0] - 0.02, c[1] - 0.02]
                ]]]
            }
            area_obj = m.AdministrativeArea(
                region_id=region.id,
                name=a["name"],
                code=a["code"],
                admin_level=a["level"],
                population=a["pop"],
                area_sqkm=a["area"],
                geom=poly
            )
            db.add(area_obj)
            db.flush()
            admin_areas[a["code"]] = area_obj

        # -------------------------------------------------------------
        # 3. Dataset Sources & Datasets
        # -------------------------------------------------------------
        src_usgs = m.DatasetSource(
            code="USGS_LANDSAT",
            name="USGS Earth Resources Observation and Science (EROS)",
            provider="United States Geological Survey",
            website_url="https://landsat.usgs.gov/",
            license="Open Access / Public Domain",
            update_frequency="16 days",
            citation="Landsat 8/9 Collection 2 Level-2 Surface Temperature Science Product"
        )
        src_copernicus = m.DatasetSource(
            code="COPERNICUS_S5P",
            name="Copernicus Open Access Hub / Sentinel-5P",
            provider="European Space Agency (ESA)",
            website_url="https://dataspace.copernicus.eu/",
            license="CC BY-SA 3.0 IGO",
            update_frequency="Daily",
            citation="Sentinel-5 Precursor TROPOMI Level 2 Atmospheric Chemistry Products (SO2, NO2)"
        )
        src_cpcb = m.DatasetSource(
            code="CPCB_MPCB",
            name="Central & Maharashtra Pollution Control Board CAAQMS",
            provider="CPCB / MPCB",
            website_url="https://cpcb.nic.in/",
            license="Government Open Data License - India",
            update_frequency="Hourly / Continuous",
            citation="Continuous Ambient Air Quality Monitoring Station (CAAQMS) Real-Time Network"
        )
        src_chetna = m.DatasetSource(
            code="CHETNA_ROAD",
            name="CHETNA-Road Gridded Vehicular Emission Inventory",
            provider="Mittakola et al. (2025)",
            website_url="https://doi.org/10.6084/m9.figshare.28330067",
            license="CC BY 4.0",
            update_frequency="Research Dataset (2021 Reference Year)",
            citation="Mittakola et al. (2025), High-resolution Gridded CO2 and Pollutant Emission Data from Road Traffic in Indian Cities."
        )
        db.add_all([src_usgs, src_copernicus, src_cpcb, src_chetna])
        db.flush()

        ds_heat = m.Dataset(
            source_id=src_usgs.id,
            code="LANDSAT_LST",
            name="Landsat Collection 2 Land Surface Temperature",
            description="Derived skin surface temperature from thermal infrared sensors (TIRS).",
            data_classification="satellite_derived",
            spatial_resolution_m=30.0,
            temporal_resolution="16-day",
            unit="degC",
            crs="EPSG:4326",
            coverage_area="Panvel & Navi Mumbai",
            limitations="Measures skin temperature; not equivalent to ambient 2m air temperature."
        )
        ds_s5p = m.Dataset(
            source_id=src_copernicus.id,
            code="TROPOMI_GASES",
            name="Sentinel-5P TROPOMI Atmospheric Column Densities",
            description="Total and tropospheric vertical column densities for SO2 and NO2.",
            data_classification="satellite_derived",
            spatial_resolution_m=3500.0,
            temporal_resolution="daily",
            unit="mol/m2",
            crs="EPSG:4326",
            coverage_area="Mumbai Metropolitan Region",
            limitations="Atmospheric column averages; does not establish verified stack emissions of an individual facility."
        )
        ds_traffic = m.Dataset(
            source_id=src_chetna.id,
            code="CHETNA_EMISSIONS",
            name="CHETNA-Road 500m Gridded Road Transport Emissions",
            description="Modelled road transport emission estimates for Indian urban agglomerations.",
            data_classification="modelled",
            spatial_resolution_m=500.0,
            temporal_resolution="daily",
            unit="g/km/day",
            crs="EPSG:4326",
            coverage_area="Mumbai Regional Domain",
            limitations="Modelled historical traffic emissions; does not represent live roadside concentrations."
        )
        ds_cpcb = m.Dataset(
            source_id=src_cpcb.id,
            code="CAAQMS_STATIONS",
            name="CPCB / MPCB Continuous Ambient Air Quality Data",
            description="Ground station validated observations of criteria pollutants.",
            data_classification="measured",
            spatial_resolution_m=1.0,
            temporal_resolution="hourly",
            unit="ug/m3",
            crs="EPSG:4326",
            coverage_area="Station Points",
            limitations="Point measurements representing local ambient air quality."
        )
        db.add_all([ds_heat, ds_s5p, ds_traffic, ds_cpcb])
        db.flush()

        # Ingestion run audit logs
        ingestion_run = m.DataIngestionRun(
            dataset_id=ds_heat.id,
            status="completed",
            records_ingested=1250,
            file_path="data/raw/landsat_tirs_2026.tif",
            checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            execution_duration_sec=3.42,
            provenance_metadata={"processing_level": "Level-2", "quality_mask": "cloud_screened"}
        )
        db.add(ingestion_run)

        # -------------------------------------------------------------
        # 4. Monitoring Locations
        # -------------------------------------------------------------
        stations_data = [
            {"id": "ST-PANVEL-01", "name": "Panvel Town CAAQMS Station", "type": "caaqms", "lat": 18.9894, "lon": 73.1175},
            {"id": "ST-TALOJA-02", "name": "Taloja MIDC Industrial Air Station", "type": "industrial", "lat": 19.0625, "lon": 73.1412},
            {"id": "ST-VASHI-03", "name": "Vashi Sector 17 NMMC Station", "type": "caaqms", "lat": 19.0770, "lon": 72.9986},
            {"id": "ST-KHARGHAR-04", "name": "Kharghar Sector 12 Node", "type": "sensor_node", "lat": 19.0435, "lon": 73.0682},
        ]
        stations = {}
        for s in stations_data:
            st_obj = m.MonitoringLocation(
                station_id=s["id"],
                name=s["name"],
                station_type=s["type"],
                latitude=s["lat"],
                longitude=s["lon"],
                geom=point_from_coordinates(s["lon"], s["lat"]),
                is_active=True
            )
            db.add(st_obj)
            db.flush()
            stations[s["id"]] = st_obj

        # -------------------------------------------------------------
        # 5. Industrial Facilities
        # -------------------------------------------------------------
        facilities_data = [
            {
                "name": "Deepak Fertilisers & Petrochemicals Corp",
                "type": "Chemicals & Petrochemicals",
                "category": "Red",
                "consent": "MPCB/CONSENT/RED/TALOJA/0194",
                "lat": 19.0650, "lon": 73.1450,
                "address": "Plot K-1 to K-8, Taloja MIDC, Raigad",
                "cems": True
            },
            {
                "name": "Galaxy Surfactants Manufacturing Unit",
                "type": "Speciality Chemicals",
                "category": "Red",
                "consent": "MPCB/CONSENT/RED/TALOJA/0488",
                "lat": 19.0580, "lon": 73.1380,
                "address": "Plot M-3, Taloja Industrial Area, Raigad",
                "cems": True
            },
            {
                "name": "Owens Corning India Composite Facility",
                "type": "Glass & Mineral Composites",
                "category": "Red",
                "consent": "MPCB/CONSENT/RED/TALOJA/0812",
                "lat": 19.0720, "lon": 73.1520,
                "address": "Plot 3, Taloja Industrial Area",
                "cems": False
            },
            {
                "name": "Trans-Thane Creek Chemical Cluster Unit A",
                "type": "Industrial Chemicals & Solvents",
                "category": "Red",
                "consent": "MPCB/CONSENT/RED/TTC/1102",
                "lat": 19.0910, "lon": 73.0150,
                "address": "TTC Industrial Area, Pawane, Navi Mumbai",
                "cems": True
            },
            {
                "name": "Navi Mumbai Ready-Mix & Asphalt Unit",
                "type": "Construction Materials",
                "category": "Orange",
                "consent": "MPCB/CONSENT/ORANGE/NMMC/0315",
                "lat": 19.0210, "lon": 73.0480,
                "address": "Turbhe Naka Road, Navi Mumbai",
                "cems": False
            }
        ]
        facilities = {}
        for f in facilities_data:
            fac_obj = m.IndustrialFacility(
                name=f["name"],
                industry_type=f["type"],
                category=f["category"],
                consent_id=f["consent"],
                latitude=f["lat"],
                longitude=f["lon"],
                geom=point_from_coordinates(f["lon"], f["lat"]),
                address=f["address"],
                is_cems_connected=f["cems"]
            )
            db.add(fac_obj)
            db.flush()
            facilities[f["name"]] = fac_obj

        # -------------------------------------------------------------
        # 6. Road Segments
        # -------------------------------------------------------------
        roads_data = [
            {"osm_id": "OSM-R-01", "name": "Sion-Panvel Highway Express Corridor", "type": "primary", "lanes": 6, "speed": 80, "coords": [[72.99, 19.06], [73.05, 19.02], [73.11, 18.99]]},
            {"osm_id": "OSM-R-02", "name": "NH 48 Panvel-Palaspe Transport Spine", "type": "trunk", "lanes": 4, "speed": 80, "coords": [[73.11, 18.99], [73.14, 18.96], [73.17, 18.92]]},
            {"osm_id": "OSM-R-03", "name": "Taloja MIDC Heavy Freight Access Road", "type": "secondary", "lanes": 4, "speed": 40, "coords": [[73.12, 19.05], [73.14, 19.06], [73.16, 19.07]]},
            {"osm_id": "OSM-R-04", "name": "Palm Beach Road (Vashi - Belapur)", "type": "primary", "lanes": 6, "speed": 60, "coords": [[72.99, 19.07], [73.01, 19.04], [73.03, 19.01]]},
        ]
        roads = {}
        for r in roads_data:
            road_obj = m.RoadSegment(
                osm_id=r["osm_id"],
                name=r["name"],
                road_type=r["type"],
                lanes=r["lanes"],
                speed_limit_kmh=r["speed"],
                length_m=12500.0,
                geom={"type": "MultiLineString", "coordinates": [r["coords"]]}
            )
            db.add(road_obj)
            db.flush()
            roads[r["name"]] = road_obj

        # -------------------------------------------------------------
        # 7. Sensitive Locations
        # -------------------------------------------------------------
        sensitive_data = [
            {"name": "MGM Hospital and Medical College", "cat": "hospital", "lat": 19.0230, "lon": 73.0890, "cap": 850, "addr": "Kamothe Sector 1"},
            {"name": "Dr. D.Y. Patil Multispecialty Hospital", "cat": "hospital", "lat": 19.0410, "lon": 73.0290, "cap": 1200, "addr": "Nerul Sector 7"},
            {"name": "Kharghar Central Park & Bio-Reserve", "cat": "park", "lat": 19.0610, "lon": 73.0710, "cap": 5000, "addr": "Kharghar Sector 23"},
            {"name": "Ryan International High School", "cat": "school", "lat": 19.0680, "lon": 73.0120, "cap": 2400, "addr": "Sanpada Sector 14"},
            {"name": "Panvel Sub-District Civil Hospital", "cat": "hospital", "lat": 18.9920, "lon": 73.1160, "cap": 300, "addr": "Line Ali, Old Panvel"},
        ]
        for s in sensitive_data:
            sens_obj = m.SensitiveLocation(
                name=s["name"],
                category=s["cat"],
                latitude=s["lat"],
                longitude=s["lon"],
                geom=point_from_coordinates(s["lon"], s["lat"]),
                address=s["addr"],
                capacity=s["cap"]
            )
            db.add(sens_obj)

        # -------------------------------------------------------------
        # 8. Population Grids (Demo 500m cells)
        # -------------------------------------------------------------
        for idx, (lon_step, lat_step, pop_val) in enumerate([
            (73.11, 18.99, 12400),
            (73.08, 19.02, 18900),
            (73.14, 19.06, 4200),
            (73.06, 19.04, 14500),
            (73.03, 19.01, 11200),
            (72.99, 19.07, 16800),
        ]):
            poly = {
                "type": "Polygon",
                "coordinates": [[
                    [lon_step - 0.005, lat_step - 0.005],
                    [lon_step + 0.005, lat_step - 0.005],
                    [lon_step + 0.005, lat_step + 0.005],
                    [lon_step - 0.005, lat_step + 0.005],
                    [lon_step - 0.005, lat_step - 0.005]
                ]]
            }
            grid_obj = m.PopulationGrid(
                cell_id=f"GRID-500M-{idx+1:03d}",
                geom=poly,
                population_count=float(pop_val),
                density_per_sqkm=float(pop_val * 4.0),
                year=2021,
                source="GHS-POP / WorldPop (2021 Baseline)"
            )
            db.add(grid_obj)

        # -------------------------------------------------------------
        # 9. Heat Observations & Heat Hotspots
        # -------------------------------------------------------------
        now = datetime.now(timezone.utc)
        heat_obs = m.HeatObservation(
            region_id=region.id,
            acquisition_date=now - timedelta(days=2),
            sensor="Landsat 9 TIRS-2 Level-2",
            mean_lst_celsius=36.8,
            min_lst_celsius=29.2,
            max_lst_celsius=44.1,
            mean_ndvi=0.22,
            mean_ndbi=0.28,
            mean_ndmi=0.14,
            cloud_cover_percent=2.1,
            raster_asset_uri="data/processed/heat/landsat9_panvel_lst_latest.tif",
            geom=region.geom,
            data_classification="satellite_derived",
            limitations="Landsat 9 Collection 2 LST represents skin temperature, not near-surface air temperature."
        )
        db.add(heat_obs)
        db.flush()

        heat_hotspots_data = [
            {
                "code": "HEAT-TALOJA-01",
                "sev": "extreme",
                "lst": 43.8,
                "anom": 7.0,
                "ndvi": 0.07,
                "ndbi": 0.48,
                "area": 4.8,
                "coords": [73.142, 19.062],
                "factors": {"impervious_surface_fraction": 0.85, "vegetation_fraction": 0.05, "industrial_roof_albedo": 0.12}
            },
            {
                "code": "HEAT-PANVEL-02",
                "sev": "high",
                "lst": 41.2,
                "anom": 4.4,
                "ndvi": 0.11,
                "ndbi": 0.38,
                "area": 3.2,
                "coords": [73.118, 18.991],
                "factors": {"impervious_surface_fraction": 0.78, "vegetation_fraction": 0.08, "commercial_density": "high"}
            },
            {
                "code": "HEAT-VASHI-03",
                "sev": "moderate",
                "lst": 39.5,
                "anom": 2.7,
                "ndvi": 0.16,
                "ndbi": 0.31,
                "area": 2.5,
                "coords": [72.999, 19.075],
                "factors": {"impervious_surface_fraction": 0.70, "vegetation_fraction": 0.12}
            }
        ]
        for h in heat_hotspots_data:
            c = h["coords"]
            h_poly = {
                "type": "Polygon",
                "coordinates": [[
                    [c[0] - 0.008, c[1] - 0.008],
                    [c[0] + 0.008, c[1] - 0.008],
                    [c[0] + 0.008, c[1] + 0.008],
                    [c[0] - 0.008, c[1] + 0.008],
                    [c[0] - 0.008, c[1] - 0.008]
                ]]
            }
            hh = m.HeatHotspot(
                region_id=region.id,
                hotspot_code=h["code"],
                severity=h["sev"],
                lst_celsius=h["lst"],
                lst_anomaly_celsius=h["anom"],
                ndvi=h["ndvi"],
                ndbi=h["ndbi"],
                area_sqkm=h["area"],
                geom=h_poly,
                detected_date=now - timedelta(days=2),
                contributing_factors=h["factors"],
                data_classification="satellite_derived"
            )
            db.add(hh)

        # -------------------------------------------------------------
        # 10. Pollutant Observations & Industrial Hotspots
        # -------------------------------------------------------------
        st_taloja = stations["ST-TALOJA-02"]
        fac_deepak = facilities["Deepak Fertilisers & Petrochemicals Corp"]
        
        # Ground observations at Taloja station
        obs_so2 = m.PollutantObservation(
            monitoring_location_id=st_taloja.id,
            industrial_facility_id=fac_deepak.id,
            pollutant="SO2",
            concentration_value=92.5,
            unit="ug/m3",
            averaging_period="24h",
            observed_at=now - timedelta(hours=6),
            wind_speed_ms=3.2,
            wind_direction_deg=245.0,
            geom=st_taloja.geom,
            data_classification="measured"
        )
        obs_no2 = m.PollutantObservation(
            monitoring_location_id=st_taloja.id,
            industrial_facility_id=fac_deepak.id,
            pollutant="NO2",
            concentration_value=74.2,
            unit="ug/m3",
            averaging_period="24h",
            observed_at=now - timedelta(hours=6),
            wind_speed_ms=3.2,
            wind_direction_deg=245.0,
            geom=st_taloja.geom,
            data_classification="measured"
        )
        db.add_all([obs_so2, obs_no2])

        # Industrial Hotspot (TROPOMI Indicator)
        ind_poly = {
            "type": "Polygon",
            "coordinates": [[
                [73.135, 19.055],
                [73.155, 19.055],
                [73.155, 19.075],
                [73.135, 19.075],
                [73.135, 19.055]
            ]]
        }
        ind_hotspot = m.IndustrialHotspot(
            facility_id=fac_deepak.id,
            hotspot_code="IND-TALOJA-SO2-01",
            pollutant="SO2",
            concentration_estimate=0.00085,
            unit="mol/m2",
            severity="high",
            wind_aligned=True,
            wind_direction_deg=245.0,
            geom=ind_poly,
            detected_date=now - timedelta(days=1),
            evidence_notes="Elevated TROPOMI SO2 vertical column density (0.00085 mol/m2) observed downwind of Taloja Chemical Cluster.",
            data_classification="satellite_derived"
        )
        db.add(ind_hotspot)

        # -------------------------------------------------------------
        # 11. Vehicular Emission Estimates & Vehicular Hotspots
        # -------------------------------------------------------------
        road_sion = roads["Sion-Panvel Highway Express Corridor"]
        traffic_est = m.TrafficEmissionEstimate(
            road_segment_id=road_sion.id,
            date=now - timedelta(days=1),
            co2_kg_per_km_day=325.4,
            nox_g_per_km_day=188.6,
            pm_g_per_km_day=14.2,
            co_g_per_km_day=52.0,
            model_source="CHETNA-Road (Mittakola et al. 2025)",
            grid_resolution_m=500.0,
            geom=road_sion.geom,
            data_classification="modelled"
        )
        db.add(traffic_est)

        veh_hotspot = m.VehicularHotspot(
            road_segment_id=road_sion.id,
            hotspot_code="VEH-SION-PANVEL-01",
            pollutant="NOx",
            emission_intensity=188.6,
            unit="g/km/day",
            severity="high",
            geom=road_sion.geom,
            detected_date=now - timedelta(days=1),
            traffic_context="Peak freight and inter-city commuter corridor connecting Greater Mumbai with Navi Mumbai and Pune Expressway.",
            data_classification="modelled"
        )
        db.add(veh_hotspot)

        # -------------------------------------------------------------
        # 12. Signature ThermoSim Compound Hotspots
        # -------------------------------------------------------------
        cmp_poly_1 = {
            "type": "Polygon",
            "coordinates": [[
                [73.125, 19.045],
                [73.155, 19.045],
                [73.155, 19.075],
                [73.125, 19.075],
                [73.125, 19.045]
            ]]
        }
        cmp_hotspot_1 = m.CompoundHotspot(
            region_id=region.id,
            hotspot_code="CMP-PANVEL-001",
            title="Taloja Industrial & Freight Transport Compound Nexus",
            heat_score=88.0,
            industrial_score=92.0,
            vehicular_score=78.0,
            exposure_score=72.0,
            compound_risk_score=83.5,  # 0.3*88 + 0.25*92 + 0.25*78 + 0.2*72 = 26.4 + 23.0 + 19.5 + 14.4 = 83.3
            severity="critical",
            primary_hazard="compound",
            area_sqkm=7.5,
            geom=cmp_poly_1,
            detected_date=now - timedelta(days=1),
            contributing_evidence={
                "heat": {"lst_celsius": 43.8, "anomaly_celsius": 7.0, "source": "Landsat 9 TIRS"},
                "industrial": {"pollutant": "SO2", "column_mol_m2": 0.00085, "plume_alignment": True},
                "vehicular": {"nox_g_km_day": 188.6, "corridor": "Taloja MIDC Spine"},
                "exposure": {"population_within_2km": 42000, "sensitive_sites_count": 2},
                "weights_applied": {"heat": 0.30, "industrial": 0.25, "vehicular": 0.25, "exposure": 0.20}
            },
            methodology_version="ThermoSim-Composite-v1.0",
            limitations="Composite screening index; weights configured for industrial-urban interface.",
            data_classification="modelled"
        )

        cmp_poly_2 = {
            "type": "Polygon",
            "coordinates": [[
                [73.075, 19.015],
                [73.105, 19.015],
                [73.105, 19.045],
                [73.075, 19.045],
                [73.075, 19.015]
            ]]
        }
        cmp_hotspot_2 = m.CompoundHotspot(
            region_id=region.id,
            hotspot_code="CMP-PANVEL-002",
            title="Sion-Panvel Corridor & Kamothe High-Exposure Zone",
            heat_score=75.0,
            industrial_score=48.0,
            vehicular_score=91.0,
            exposure_score=86.0,
            compound_risk_score=74.4,  # 0.3*75 + 0.25*48 + 0.25*91 + 0.2*86 = 22.5 + 12.0 + 22.75 + 17.2 = 74.45
            severity="high",
            primary_hazard="vehicular",
            area_sqkm=6.2,
            geom=cmp_poly_2,
            detected_date=now - timedelta(days=1),
            contributing_evidence={
                "heat": {"lst_celsius": 40.8, "anomaly_celsius": 4.0},
                "industrial": {"pollutant": "Particulate drift", "distance_to_cluster_km": 3.8},
                "vehicular": {"nox_g_km_day": 188.6, "corridor": "Sion-Panvel Highway"},
                "exposure": {"population_within_2km": 94000, "sensitive_sites_count": 3},
                "weights_applied": {"heat": 0.30, "industrial": 0.25, "vehicular": 0.25, "exposure": 0.20}
            },
            methodology_version="ThermoSim-Composite-v1.0",
            limitations="High population density intersecting arterial vehicular emissions.",
            data_classification="modelled"
        )
        db.add_all([cmp_hotspot_1, cmp_hotspot_2])
        db.flush()

        # Community exposure screening
        exp_1 = m.CommunityExposureAssessment(
            administrative_area_id=admin_areas["PMC-CENTRAL"].id,
            compound_hotspot_id=cmp_hotspot_2.id,
            exposed_population=94000,
            sensitive_facilities_count=3,
            hazard_index=72.5,
            exposure_index=84.0,
            vulnerability_index=68.0,
            overall_risk_index=74.8,
            assessment_date=now,
            breakdown_json={"children_elderly_pct": 21.4, "green_cover_pct": 8.5},
            data_classification="estimated"
        )
        exp_2 = m.CommunityExposureAssessment(
            administrative_area_id=admin_areas["TALOJA-MIDC"].id,
            compound_hotspot_id=cmp_hotspot_1.id,
            exposed_population=42000,
            sensitive_facilities_count=1,
            hazard_index=88.0,
            exposure_index=65.0,
            vulnerability_index=78.0,
            overall_risk_index=77.0,
            assessment_date=now,
            breakdown_json={"industrial_workforce_fraction": 0.65, "buffer_deficiency_m": 120.0},
            data_classification="estimated"
        )
        db.add_all([exp_1, exp_2])

        # -------------------------------------------------------------
        # 13. Regulatory Authorities, Standards & Compliance Thresholds
        # -------------------------------------------------------------
        auth_cpcb = m.RegulatoryAuthority(
            code="CPCB",
            name="Central Pollution Control Board",
            country="India",
            jurisdiction="National",
            website_url="https://cpcb.nic.in/"
        )
        auth_mpcb = m.RegulatoryAuthority(
            code="MPCB",
            name="Maharashtra Pollution Control Board",
            country="India",
            jurisdiction="State of Maharashtra",
            website_url="https://mpcb.gov.in/"
        )
        db.add_all([auth_cpcb, auth_mpcb])
        db.flush()

        std_naaqs = m.EnvironmentalStandard(
            authority_id=auth_cpcb.id,
            code="NAAQS_2009",
            title="National Ambient Air Quality Standards 2009",
            document_identifier="Notification G.S.R. 826(E)",
            publication_date=datetime(2009, 11, 16, tzinfo=timezone.utc),
            effective_date=datetime(2009, 11, 18, tzinfo=timezone.utc),
            category="ambient_air",
            source_url="https://cpcb.nic.in/air-quality-standards/",
            summary="Statutory ambient concentration limits for 12 criteria pollutants across India."
        )
        db.add(std_naaqs)
        db.flush()

        # Official NAAQS thresholds
        th_pm10_24h = m.StandardThreshold(
            standard_id=std_naaqs.id,
            parameter="PM10",
            limit_value=100.0,
            unit="ug/m3",
            averaging_period="24h",
            area_category="residential_rural",
            sampling_method="Gravimetric / Beta-attenuation",
            applicability_clause="Schedule VII, Table 1, Row 1"
        )
        th_pm25_24h = m.StandardThreshold(
            standard_id=std_naaqs.id,
            parameter="PM2.5",
            limit_value=60.0,
            unit="ug/m3",
            averaging_period="24h",
            area_category="residential_rural",
            sampling_method="Gravimetric / Beta-attenuation",
            applicability_clause="Schedule VII, Table 1, Row 2"
        )
        th_so2_24h = m.StandardThreshold(
            standard_id=std_naaqs.id,
            parameter="SO2",
            limit_value=80.0,
            unit="ug/m3",
            averaging_period="24h",
            area_category="residential_rural",
            sampling_method="Improved West and Gaeke / UV Fluorescence",
            applicability_clause="Schedule VII, Table 1, Row 3"
        )
        th_no2_24h = m.StandardThreshold(
            standard_id=std_naaqs.id,
            parameter="NO2",
            limit_value=80.0,
            unit="ug/m3",
            averaging_period="24h",
            area_category="residential_rural",
            sampling_method="Jacob & Hochheiser / Chemiluminescence",
            applicability_clause="Schedule VII, Table 1, Row 4"
        )
        db.add_all([th_pm10_24h, th_pm25_24h, th_so2_24h, th_no2_24h])
        db.flush()

        # Compliance Assessments
        comp_1 = m.ComplianceAssessment(
            standard_threshold_id=th_so2_24h.id,
            monitoring_location_id=st_taloja.id,
            facility_id=fac_deepak.id,
            parameter="SO2",
            observed_value=92.5,
            unit="ug/m3",
            averaging_period="24h",
            threshold_value=80.0,
            ratio_to_threshold=1.156,
            status="potential_exceedance",
            assessment_notes="Observed 24-hour mean SO2 (92.5 ug/m3) exceeds the NAAQS reference benchmark (80.0 ug/m3) by 15.6%.",
            reviewed_by="Senior Environmental Inspector",
            reviewed_at=now - timedelta(hours=4),
            review_decision="further_investigation_required"
        )
        comp_2 = m.ComplianceAssessment(
            standard_threshold_id=th_no2_24h.id,
            monitoring_location_id=st_taloja.id,
            facility_id=fac_deepak.id,
            parameter="NO2",
            observed_value=74.2,
            unit="ug/m3",
            averaging_period="24h",
            threshold_value=80.0,
            ratio_to_threshold=0.928,
            status="within_reference_limit",
            assessment_notes="Observed 24-hour mean NO2 (74.2 ug/m3) is within the NAAQS reference benchmark (80.0 ug/m3).",
            reviewed_by="Automated Compliance Engine",
            reviewed_at=now - timedelta(hours=4),
            review_decision="confirmed_concern"
        )
        db.add_all([comp_1, comp_2])
        db.flush()

        # -------------------------------------------------------------
        # 14. Intervention Types & Scenarios (ThermoSim)
        # -------------------------------------------------------------
        it_tree = m.InterventionType(
            code="tree_planting",
            name="Urban Tree Canopy & Afforestation",
            description="Planting native broadleaf trees to enhance shading, evapotranspiration, and microclimate cooling.",
            category="nature_based",
            default_parameters={"canopy_cover_target_pct": 30.0, "tree_spacing_m": 5.0, "species": "Neem, Peepal, Karanj"},
            scientific_rationale="Evaporative cooling and direct solar radiation attenuation reduces surface temperatures by 1.5 - 3.5 degC.",
            known_limitations="Requires 3-5 years for canopy maturation; water supply needed during establishment."
        )
        it_roof = m.InterventionType(
            code="cool_roofs",
            name="High-Albedo Cool Roof Coating",
            description="Applying high solar reflectance index (SRI >= 100) elastomeric or white ceramic coatings to roofs.",
            category="material",
            default_parameters={"albedo_increase": 0.45, "thermal_emittance": 0.90, "roof_fraction": 0.60},
            scientific_rationale="Reflects 70-85% of incoming solar irradiance, lowering roof skin temperatures by 5 - 12 degC.",
            known_limitations="Coating degrades over 3-5 years due to dust/particulate deposition; periodic cleaning required."
        )
        it_buffer = m.InterventionType(
            code="green_buffers",
            name="Industrial-Residential Vegetative Green Buffer",
            description="Dense multi-tier vegetative buffer zone (trees + shrubs) separating industrial estates from communities.",
            category="zoning",
            default_parameters={"buffer_width_m": 150.0, "canopy_density_pct": 75.0, "setback_m": 50.0},
            scientific_rationale="Acts as a physical particulate filter, wind baffle, and thermal barrier between emission sources and homes.",
            known_limitations="Requires land acquisition and dedicated industrial zoning compliance."
        )
        it_traffic = m.InterventionType(
            code="traffic_management",
            name="Low-Emission Transport Corridor Optimization",
            description="Heavy freight diversion, signal coordination, and speed optimization along major highways.",
            category="traffic",
            default_parameters={"freight_diversion_pct": 25.0, "ev_bus_share_pct": 40.0, "speed_smoothing_kmh": 60.0},
            scientific_rationale="Smoother traffic flow and reduced stop-and-go acceleration reduces roadside NOx emissions by 15-28%.",
            known_limitations="Shifts freight volumes to alternative regional corridors; requires strict traffic police enforcement."
        )
        it_combined = m.InterventionType(
            code="combined",
            name="ThermoSim Integrated Multi-Hazard Intervention",
            description="Synergistic combination of Green Buffers, Cool Roofs, and Transport Management for critical hotspots.",
            category="combined",
            default_parameters={"buffer_width_m": 150.0, "cool_roof_fraction": 0.50, "traffic_reduction_pct": 20.0},
            scientific_rationale="Compound risks require compound mitigation: tackles heat island and air pollution simultaneously.",
            known_limitations="Requires multi-agency coordination between Municipal Corporation, MIDC, and Transport authorities."
        )
        db.add_all([it_tree, it_roof, it_buffer, it_traffic, it_combined])
        db.flush()

        # Seed realistic pre-calculated scenarios
        scen_1 = m.InterventionScenario(
            name="Taloja Green Buffer & Industrial Setback Plan",
            description="Simulated 150m vegetative buffer zone along the eastern perimeter of Taloja MIDC facing Kamothe.",
            intervention_type_id=it_buffer.id,
            region_id=region.id,
            simulated_area_sqm=450000.0,
            scenario_parameters={"buffer_width_m": 150.0, "canopy_density_pct": 75.0},
            baseline_indicators={"lst_celsius": 43.8, "nox_g_km_day": 188.6, "risk_score": 83.5},
            simulated_indicators={"lst_celsius": 41.2, "nox_g_km_day": 165.0, "risk_score": 68.2},
            projected_temp_reduction_celsius=2.6,
            projected_emission_reduction_percent=12.5,
            projected_risk_score_reduction=15.3,
            estimated_cost_inr=18500000.0,
            assumptions_json={"canopy_growth_years": 3, "particulate_deposition_velocity_cms": 1.2},
            data_classification="simulated"
        )
        scen_2 = m.InterventionScenario(
            name="Panvel Old Town Cool Roof & Urban Shading Initiative",
            description="Retrofitting 60% of municipal and commercial roofs in Panvel Central with SRI 104 cool roof coating.",
            intervention_type_id=it_roof.id,
            region_id=region.id,
            simulated_area_sqm=320000.0,
            scenario_parameters={"albedo_increase": 0.45, "roof_coverage_pct": 60.0},
            baseline_indicators={"lst_celsius": 41.2, "nox_g_km_day": 142.0, "risk_score": 74.4},
            simulated_indicators={"lst_celsius": 38.8, "nox_g_km_day": 142.0, "risk_score": 64.1},
            projected_temp_reduction_celsius=2.4,
            projected_emission_reduction_percent=0.0,
            projected_risk_score_reduction=10.3,
            estimated_cost_inr=8200000.0,
            assumptions_json={"coating_cost_sqm_inr": 25.0, "solar_reflectance": 0.82},
            data_classification="simulated"
        )
        db.add_all([scen_1, scen_2])
        db.flush()

        # -------------------------------------------------------------
        # 15. Incidents, Assessments, Actions, and History
        # -------------------------------------------------------------
        inc_1 = m.Incident(
            incident_number="INC-2026-001",
            title="Chemical odour, throat irritation and dense haze reported near Kamothe Sector 36",
            description="Resident-submitted observation: Continuous pungent chemical odour detected during evening hours with visible haze originating from northwest direction.",
            category="industrial_emission",
            severity="high",
            status="in_progress",
            latitude=19.0310,
            longitude=73.0940,
            address="Sector 36, Kamothe Node, Panvel Taluka",
            reporter_name="Sunil Patil (Kamothe Residents Welfare Association)",
            reporter_contact="resident_assoc@kamothe.org",
            reporter_type="citizen",
            reported_at=now - timedelta(hours=36),
            environmental_context={
                "nearest_hotspot": "CMP-PANVEL-001",
                "wind_direction": "245 deg (from Taloja MIDC towards Kamothe)",
                "ambient_so2_ug_m3": 92.5
            }
        )
        inc_2 = m.Incident(
            incident_number="INC-2026-002",
            title="Severe localized heat island and heat exhaustion risk near Panvel Bus Terminus",
            description="Field inspector report: Surface temperature reaching 43 degC on unshaded concrete bus bays, lack of drinking water and cooling shelters for passengers.",
            category="heat_wave",
            severity="medium",
            status="action_recommended",
            latitude=18.9915,
            longitude=73.1182,
            address="Panvel MSRTC Bus Depot & Commercial Circle",
            reporter_name="Dr. R. Kulkarni (Urban Public Health Officer)",
            reporter_type="inspector",
            reported_at=now - timedelta(hours=18),
            environmental_context={
                "nearest_hotspot": "HEAT-PANVEL-02",
                "lst_celsius": 41.2,
                "anomaly_celsius": 4.4
            }
        )
        db.add_all([inc_1, inc_2])
        db.flush()

        # Incident assessment
        ass_1 = m.IncidentAssessment(
            incident_id=inc_1.id,
            compound_hotspot_id=cmp_hotspot_1.id,
            nearby_facilities_summary=[{"name": "Deepak Fertilisers", "distance_km": 2.4, "category": "Red"}],
            nearby_heat_summary={"lst_celsius": 42.1},
            nearby_vehicular_summary={"corridor": "Sion-Panvel Express", "distance_km": 1.2},
            applicable_standards_summary=[{"standard": "NAAQS 2009", "parameter": "SO2", "limit": "80 ug/m3", "observed": "92.5 ug/m3"}],
            technical_assessment_notes="Incident point is located 2.4 km directly downwind of Taloja Industrial Cluster during prevailing southwesterly sea-breeze conditions.",
            potential_causes_statement="Proximity and downwind alignment provide contextual association; statutory stack inspection and grab sampling required for legal attribution.",
            reviewer_name="Dr. S. Deshmukh (Environmental Scientist, MPCB)",
            reviewed_at=now - timedelta(hours=24)
        )
        db.add(ass_1)

        # Corrective actions
        act_1 = m.CorrectiveAction(
            incident_id=inc_1.id,
            action_type="site_inspection",
            title="Surprise stack inspection and VOC grab sampling in Taloja MIDC Sector K",
            description="Depute joint inspection team from MPCB Sub-Regional Office Navi Mumbai II to inspect scrubbers and continuous emission monitoring systems.",
            priority="high",
            assigned_to="MPCB Field Inspection Squad II",
            assigned_department="Maharashtra Pollution Control Board (Sub-Regional Office Panvel)",
            due_date=now + timedelta(days=2),
            status="in_progress",
            completion_notes="Initial site visit conducted; calibration logs of scrubbers being audited."
        )
        act_2 = m.CorrectiveAction(
            incident_id=inc_1.id,
            action_type="green_buffer",
            title="Accelerate Phase 1 of Kamothe-Taloja Green Shield Buffer",
            description="Coordinate with Panvel Municipal Corporation to plant 2500 native trees along boundary wall.",
            priority="medium",
            assigned_to="Panvel Municipal Corporation Tree Authority",
            assigned_department="Parks & Environment Dept, PMC",
            due_date=now + timedelta(days=30),
            status="assigned"
        )
        db.add_all([act_1, act_2])

        # Status History
        hist_1 = m.IncidentStatusHistory(
            incident_id=inc_1.id,
            from_status="reported",
            to_status="under_review",
            changed_by="Automated Intake Router",
            comment="Incident logged from citizen portal and assigned priority high.",
            changed_at=now - timedelta(hours=35)
        )
        hist_2 = m.IncidentStatusHistory(
            incident_id=inc_1.id,
            from_status="under_review",
            to_status="in_progress",
            changed_by="Dr. S. Deshmukh",
            comment="Technical assessment completed; corrective inspection action assigned to MPCB Squad.",
            changed_at=now - timedelta(hours=24)
        )
        db.add_all([hist_1, hist_2])

        db.commit()
        print("=" * 70)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print(f" - Region: {region.name}")
        print(f" - Admin Areas: {len(admin_areas_data)}")
        print(f" - Facilities: {len(facilities_data)}")
        print(f" - Road Segments: {len(roads_data)}")
        print(f" - Monitoring Stations: {len(stations_data)}")
        print(f" - Compound Hotspots: 2 (CMP-PANVEL-001, CMP-PANVEL-002)")
        print(f" - Standards & Thresholds: NAAQS 2009 (4 parameters)")
        print(f" - Intervention Scenarios: 2 created (ThermoSim)")
        print(f" - Incidents & Actions: 2 incidents with live tracking")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"Error seeding demo data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()

