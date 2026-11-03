"""
THERMOS AI - Custom Exception Classes

Domain-specific exceptions for clear error handling and communication.
"""

from typing import Any, Dict, Optional


class ThermosBaseException(Exception):
    """Base exception for all THERMOS AI exceptions."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(ThermosBaseException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=422
        )


class ResourceNotFoundError(ThermosBaseException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
            status_code=404
        )


class DataClassificationError(ThermosBaseException):
    """Raised when data classification is invalid or missing."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATA_CLASSIFICATION_ERROR",
            details=details,
            status_code=422
        )


class SpatialOperationError(ThermosBaseException):
    """Raised when a spatial/GIS operation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="SPATIAL_OPERATION_ERROR",
            details=details,
            status_code=400
        )


class DataIngestionError(ThermosBaseException):
    """Raised when data ingestion fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATA_INGESTION_ERROR",
            details=details,
            status_code=422
        )


class ModelNotFoundError(ThermosBaseException):
    """Raised when a requested ML model is not found."""
    
    def __init__(self, model_name: str, version: Optional[str] = None):
        details = {"model_name": model_name}
        if version:
            details["version"] = version
            message = f"Model '{model_name}' version '{version}' not found"
        else:
            message = f"Model '{model_name}' not found"
        
        super().__init__(
            message=message,
            code="MODEL_NOT_FOUND",
            details=details,
            status_code=404
        )


class PredictionError(ThermosBaseException):
    """Raised when ML prediction fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="PREDICTION_ERROR",
            details=details,
            status_code=500
        )


class ComplianceAssessmentError(ThermosBaseException):
    """Raised when compliance assessment fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="COMPLIANCE_ASSESSMENT_ERROR",
            details=details,
            status_code=422
        )


class InsufficientDataError(ThermosBaseException):
    """Raised when insufficient data is available for operation."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INSUFFICIENT_DATA",
            details=details,
            status_code=422
        )


class ExternalServiceError(ThermosBaseException):
    """Raised when external service call fails."""
    
    def __init__(
        self,
        service: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        full_details = {"service": service}
        if details:
            full_details.update(details)
        
        super().__init__(
            message=f"External service '{service}' error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details=full_details,
            status_code=502
        )


class ConfigurationError(ThermosBaseException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details=details,
            status_code=500
        )


class DatabaseError(ThermosBaseException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details=details,
            status_code=500
        )
