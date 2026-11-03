"""
THERMOS AI - Database Initialization Script

Creates all relational and spatial tables according to the declarative schema.
Supports both PostgreSQL + PostGIS (via Docker/cloud) and local SQLite.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import engine
import app.db.models  # Ensure all models are registered

logger = get_logger(__name__)


def init_database() -> None:
    """Initialize database tables."""
    logger.info("Initializing database schema...", database_url=settings.DATABASE_URL.split("@")[-1])
    try:
        Base.metadata.create_all(bind=engine)
        table_names = list(Base.metadata.tables.keys())
        logger.info(
            "Database tables created successfully",
            total_tables=len(table_names),
            tables=sorted(table_names)
        )
        print(f"Successfully initialized {len(table_names)} tables in {settings.DATABASE_URL.split('@')[-1]}")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        print(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()

