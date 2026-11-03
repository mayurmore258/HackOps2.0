"""
THERMOS AI - Database Session Management

Connection pooling and session management supporting both:
- PostgreSQL with PostGIS in production/container
- SQLite in local development/testing fallback
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Configure engine parameters based on database type
engine_kwargs = {
    "echo": settings.DATABASE_ECHO,
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["poolclass"] = QueuePool

# Create database engine
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Enable PostGIS extension for PostgreSQL connections
if not is_sqlite:
    @event.listens_for(engine, "connect")
    def enable_postgis(dbapi_conn, connection_record):
        """Enable PostGIS extension on new PostgreSQL connections."""
        cursor = dbapi_conn.cursor()
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
            dbapi_conn.commit()
        except Exception as e:
            logger.warning("Could not enable PostGIS extensions", error=str(e))
        finally:
            cursor.close()

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database sessions in FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_context() -> Session:
    """Session factory for standalone scripts and background tasks."""
    return SessionLocal()
