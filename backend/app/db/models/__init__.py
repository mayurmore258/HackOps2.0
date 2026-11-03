"""
THERMOS AI - Database Models Package

Re-exports all database models across spatial, datasets, hotspots, ML, interventions, compliance, and incidents.
"""

from app.db.base import Base, GUID, SpatialGeometry, TimestampMixin, UUIDMixin, SoftDeleteMixin

# Spatial / Geographic models
from app.db.models.spatial import (
    Region,
    AdministrativeArea,
    MonitoringLocation,
    IndustrialFacility,
    RoadSegment,
    SensitiveLocation,
    PopulationGrid,
)

# Datasets & Observations
from app.db.models.datasets import (
    DatasetSource,
    Dataset,
    DataIngestionRun,
    EnvironmentalObservation,
    HeatObservation,
    PollutantObservation,
    TrafficEmissionEstimate,
)

# Hotspots & Compound Intelligence
from app.db.models.hotspots import (
    HeatHotspot,
    IndustrialHotspot,
    VehicularHotspot,
    CompoundHotspot,
    CommunityExposureAssessment,
    RiskAssessment,
)

# AI/ML
from app.db.models.ml import (
    ModelRegistry,
    ModelTrainingRun,
    EnvironmentalPrediction,
)

# Interventions
from app.db.models.interventions import (
    InterventionType,
    InterventionScenario,
    ScenarioComparison,
)

# Compliance
from app.db.models.compliance import (
    RegulatoryAuthority,
    EnvironmentalStandard,
    StandardThreshold,
    ComplianceAssessment,
    ComplianceEvidence,
)

# Incidents & Actions
from app.db.models.incidents import (
    Incident,
    IncidentAttachment,
    IncidentAssessment,
    CorrectiveAction,
    IncidentStatusHistory,
    AuditLog,
)

__all__ = [
    "Base",
    "GUID",
    "SpatialGeometry",
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    # Spatial
    "Region",
    "AdministrativeArea",
    "MonitoringLocation",
    "IndustrialFacility",
    "RoadSegment",
    "SensitiveLocation",
    "PopulationGrid",
    # Datasets
    "DatasetSource",
    "Dataset",
    "DataIngestionRun",
    "EnvironmentalObservation",
    "HeatObservation",
    "PollutantObservation",
    "TrafficEmissionEstimate",
    # Hotspots
    "HeatHotspot",
    "IndustrialHotspot",
    "VehicularHotspot",
    "CompoundHotspot",
    "CommunityExposureAssessment",
    "RiskAssessment",
    # ML
    "ModelRegistry",
    "ModelTrainingRun",
    "EnvironmentalPrediction",
    # Interventions
    "InterventionType",
    "InterventionScenario",
    "ScenarioComparison",
    # Compliance
    "RegulatoryAuthority",
    "EnvironmentalStandard",
    "StandardThreshold",
    "ComplianceAssessment",
    "ComplianceEvidence",
    # Incidents
    "Incident",
    "IncidentAttachment",
    "IncidentAssessment",
    "CorrectiveAction",
    "IncidentStatusHistory",
    "AuditLog",
]

