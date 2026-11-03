"""
THERMOS AI - API Router Aggregator

Version 1 API router combining all domain-specific routers.
"""

from fastapi import APIRouter

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.heat import router as heat_router
from app.api.v1.industrial import router as industrial_router
from app.api.v1.vehicular import router as vehicular_router
from app.api.v1.hotspots import router as hotspots_router
from app.api.v1.community import router as community_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.interventions import router as interventions_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.datasets import router as datasets_router

api_router = APIRouter(prefix="/api/v1")

# Include all domain routers
api_router.include_router(dashboard_router)
api_router.include_router(heat_router)
api_router.include_router(industrial_router)
api_router.include_router(vehicular_router)
api_router.include_router(hotspots_router)
api_router.include_router(community_router)
api_router.include_router(predictions_router)
api_router.include_router(interventions_router)
api_router.include_router(compliance_router)
api_router.include_router(incidents_router)
api_router.include_router(datasets_router)
