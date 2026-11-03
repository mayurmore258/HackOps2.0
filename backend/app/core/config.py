"""
THERMOS AI - Core Configuration Module

Centralized configuration using Pydantic Settings.
Loads environment variables from .env file with absolute project directory resolution.
"""

from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_ENV = BACKEND_DIR.parent / ".env"
BACKEND_ENV = BACKEND_DIR / ".env"

env_paths = [str(p) for p in [BACKEND_ENV, ROOT_ENV, ".env"] if Path(p).exists()]
DEFAULT_DB_FILE = (BACKEND_DIR / "data" / "thermos.db").resolve().as_posix()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=env_paths or ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application metadata
    APP_NAME: str = "THERMOS AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # Database configuration (Defaults to local SQLite fallback if PostgreSQL is not active)
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_FILE}"
    DATABASE_ECHO: bool = False
    
    # PostgreSQL connection details (for migrations and direct connections)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "thermos_db"
    POSTGRES_USER: str = "thermos_user"
    POSTGRES_PASSWORD: str = "thermos_password"
    
    # CORS configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Security
    SECRET_KEY: str = "thermos-ai-insecure-default-key-change-in-production-123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Data storage paths
    DATA_RAW_DIR: str = str(BACKEND_DIR / "data" / "raw")
    DATA_PROCESSED_DIR: str = str(BACKEND_DIR / "data" / "processed")
    DATA_SAMPLE_DIR: str = str(BACKEND_DIR / "data" / "sample")
    ML_MODELS_DIR: str = str(BACKEND_DIR / "ml" / "saved_models")
    UPLOAD_DIR: str = str(BACKEND_DIR / "data" / "uploads")
    
    @property
    def data_raw_path(self) -> Path:
        """Get Path object for raw data directory."""
        return Path(self.DATA_RAW_DIR)
    
    @property
    def data_processed_path(self) -> Path:
        """Get Path object for processed data directory."""
        return Path(self.DATA_PROCESSED_DIR)
    
    @property
    def data_sample_path(self) -> Path:
        """Get Path object for sample data directory."""
        return Path(self.DATA_SAMPLE_DIR)
    
    @property
    def ml_models_path(self) -> Path:
        """Get Path object for ML models directory."""
        return Path(self.ML_MODELS_DIR)
    
    @property
    def upload_path(self) -> Path:
        """Get Path object for uploads directory."""
        return Path(self.UPLOAD_DIR)
    
    # Geographic configuration
    DEFAULT_SRID: int = 4326
    PROJECTED_SRID: int = 32643  # WGS 84 / UTM zone 43N (India)
    PILOT_REGION: str = "Panvel and Navi Mumbai"
    
    # External data sources (optional)
    GEE_SERVICE_ACCOUNT: Optional[str] = None
    GEE_PRIVATE_KEY_PATH: Optional[str] = None
    SENTINEL_HUB_CLIENT_ID: Optional[str] = None
    SENTINEL_HUB_CLIENT_SECRET: Optional[str] = None
    EARTHDATA_USERNAME: Optional[str] = None
    EARTHDATA_PASSWORD: Optional[str] = None
    
    # Application features
    ENABLE_DEMO_MODE: bool = True
    ENABLE_ML_PREDICTIONS: bool = True
    ENABLE_SYNTHETIC_DATA: bool = True
    
    # ML configuration
    ML_RANDOM_STATE: int = 42
    ML_TEST_SIZE: float = 0.2
    ML_CV_FOLDS: int = 5
    
    # Validation and limits
    MAX_REQUEST_SIZE_MB: int = 50
    MAX_UPLOAD_SIZE_MB: int = 100
    PAGINATION_DEFAULT_LIMIT: int = 50
    PAGINATION_MAX_LIMIT: int = 1000
    SPATIAL_QUERY_MAX_FEATURES: int = 10000
    
    # Logging
    LOG_FILE_PATH: str = str(BACKEND_DIR / "logs" / "thermos.log")
    LOG_ROTATION_SIZE_MB: int = 100
    LOG_RETENTION_DAYS: int = 30
    
    # Cache configuration (future)
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    REDIS_PASSWORD: Optional[str] = None
    
    # Monitoring (future)
    SENTRY_DSN: Optional[str] = None
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.data_raw_path,
            self.data_processed_path,
            self.data_sample_path,
            self.ml_models_path,
            self.upload_path,
            Path(self.LOG_FILE_PATH).parent,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()
