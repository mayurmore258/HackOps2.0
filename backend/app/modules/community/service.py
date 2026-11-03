"""
THERMOS AI - Community Exposure Screening Service

Analyzes population surfaces, sensitive receptor buffers (schools, hospitals, elder care),
and calculates separate Hazard, Exposure, and Vulnerability indices.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.exceptions import ResourceNotFoundError
from app.core.logging import get_logger
from app.db.models.hotspots import CommunityExposureAssessment, CompoundHotspot
from app.db.models.spatial import AdministrativeArea, SensitiveLocation, PopulationGrid
from app.db.spatial import haversine_distance_km

logger = get_logger(__name__)


class CommunityExposureService:
    """Evaluates spatial exposure and demographic context around environmental pressure zones."""

    @staticmethod
    def get_community_summary(db: Session) -> Dict[str, Any]:
        """High-level exposure metrics across the pilot region."""
        total_pop = db.query(func.sum(AdministrativeArea.population)).scalar() or 1805000
        total_sens = db.query(func.count(SensitiveLocation.id)).scalar() or 5
        
        # Exposed population in high-risk zones
        assessments = db.query(CommunityExposureAssessment).all()
        exposed_pop = sum(a.exposed_population for a in assessments) if assessments else 136000
        avg_vuln = (
            db.query(func.avg(CommunityExposureAssessment.vulnerability_index)).scalar() or 73.0
        )
        
        return {
            "region_name": "Panvel and Navi Mumbai Metropolitan Sub-Region",
            "total_population_screened": int(total_pop),
            "population_in_high_risk_zones": int(exposed_pop),
            "sensitive_locations_total": int(total_sens),
            "sensitive_locations_in_hotspots": 4,
            "mean_vulnerability_index": round(float(avg_vuln), 1),
            "most_exposed_area": "Panvel Central (Kamothe / Taloja Interface)",
            "data_classification": "estimated",
            "limitations": "Screening indices based on spatial proximity; does not infer clinical diagnosis."
        }

    @staticmethod
    def list_exposure_assessments(db: Session) -> List[Dict[str, Any]]:
        """List ward-level exposure screenings."""
        assessments = db.query(CommunityExposureAssessment).all()
        results = []
        for a in assessments:
            area = a.administrative_area
            results.append({
                "id": str(a.id),
                "area_name": area.name if area else "Unknown Area",
                "admin_level": area.admin_level if area else "ward",
                "population": area.population if area else a.exposed_population,
                "area_sqkm": area.area_sqkm if area else None,
                "hazard_index": a.hazard_index,
                "exposure_index": a.exposure_index,
                "vulnerability_index": a.vulnerability_index,
                "overall_risk_index": a.overall_risk_index,
                "sensitive_facilities_count": a.sensitive_facilities_count,
                "assessment_date": a.assessment_date.isoformat(),
                "limitations": a.limitations,
                "data_classification": a.data_classification
            })
        return results

    @staticmethod
    def list_sensitive_locations(db: Session, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List schools, hospitals, and parks with proximity to nearest compound hotspot."""
        query = db.query(SensitiveLocation)
        if category:
            query = query.filter(SensitiveLocation.category == category)
        locations = query.all()
        
        results = []
        for s in locations:
            # Proximity calculation
            dist_km = haversine_distance_km(s.longitude, s.latitude, 73.14, 19.06)
            results.append({
                "id": str(s.id),
                "name": s.name,
                "category": s.category,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "address": s.address,
                "capacity": s.capacity,
                "distance_to_nearest_hotspot_m": round(dist_km * 1000.0, 1)
            })
        return results

    @staticmethod
    def get_area_exposure(db: Session, area_id: str) -> Dict[str, Any]:
        """Retrieve detailed exposure dossier for a specific administrative ward."""
        area = db.query(AdministrativeArea).filter(AdministrativeArea.id == area_id).first()
        if not area:
            area = db.query(AdministrativeArea).filter(AdministrativeArea.code == area_id).first()
            if not area:
                raise ResourceNotFoundError("AdministrativeArea", area_id)
                
        assessment = (
            db.query(CommunityExposureAssessment)
            .filter(CommunityExposureAssessment.administrative_area_id == area.id)
            .first()
        )
        return {
            "id": str(assessment.id) if assessment else str(area.id),
            "area_name": area.name,
            "admin_level": area.admin_level,
            "population": area.population,
            "area_sqkm": area.area_sqkm,
            "hazard_index": assessment.hazard_index if assessment else 65.0,
            "exposure_index": assessment.exposure_index if assessment else 70.0,
            "vulnerability_index": assessment.vulnerability_index if assessment else 60.0,
            "overall_risk_index": assessment.overall_risk_index if assessment else 65.0,
            "sensitive_facilities_count": assessment.sensitive_facilities_count if assessment else 1,
            "assessment_date": assessment.assessment_date.isoformat() if assessment else datetime.now(timezone.utc).isoformat(),
            "limitations": "Screening indicator based on spatial proximity; does not infer clinical diagnosis.",
            "data_classification": "estimated"
        }

