"""
THERMOS AI - Pydantic Schemas Package
"""

from app.schemas.common import (
    ResponseEnvelope,
    ResponseMetadata,
    ErrorDetail,
    PaginationParams,
    PaginationMeta,
    GeoJSONGeometry,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)

from app.schemas.dashboard import (
    DashboardSummaryResponse,
    HotspotCounts,
    HighRiskLocation,
    RecentIncidentSummary,
    DatasetFreshness,
)

from app.schemas.datasets import (
    DatasetSourceResponse,
    DatasetResponse,
    DataIngestionRunResponse,
)

from app.schemas.heat import (
    HeatSummaryResponse,
    HeatHotspotItem,
    HeatTimeseriesPoint,
    HeatIndicesResponse,
    HeatAnalysisRequest,
)

from app.schemas.industrial import (
    IndustrialSummaryResponse,
    IndustrialFacilityResponse,
    IndustrialHotspotItem,
    PollutantReading,
    IndustrialEvidenceResponse,
)

from app.schemas.vehicular import (
    VehicularSummaryResponse,
    RoadSegmentResponse,
    VehicularHotspotItem,
    VehicularTimeseriesPoint,
)

from app.schemas.hotspots import (
    HotspotWeightsConfig,
    CompoundHotspotItem,
    CompoundHotspotSummaryResponse,
    HotspotsAnalyseRequest,
)

from app.schemas.community import (
    SensitiveLocationItem,
    AreaExposureItem,
    CommunitySummaryResponse,
)

from app.schemas.predictions import (
    ModelInfo,
    PredictionItem,
    PredictionSummaryResponse,
    PredictionRunRequest,
)

from app.schemas.interventions import (
    InterventionTypeResponse,
    InterventionScenarioCreate,
    InterventionScenarioResponse,
    ScenarioCompareRequest,
    ScenarioCompareResponse,
)

from app.schemas.compliance import (
    StandardThresholdResponse,
    EnvironmentalStandardResponse,
    ComplianceScreeningRequest,
    ComplianceAssessmentResponse,
    ComplianceReviewRequest,
)

from app.schemas.incidents import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    CorrectiveActionCreate,
    CorrectiveActionUpdate,
    CorrectiveActionResponse,
    StatusHistoryItem,
    IncidentAnalyseRequest,
    IncidentAnalyseResponse,
)

