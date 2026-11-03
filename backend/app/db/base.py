"""
THERMOS AI - Database Base Classes

SQLAlchemy declarative base, common mixins, and spatial integration.
"""

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Column, DateTime, String, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import CHAR, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.db.spatial import SpatialGeometry


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.
    
    Uses PostgreSQL's native UUID type, otherwise uses CHAR(36).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(str(value)))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(str(value))
            else:
                return value


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    __abstract__ = True
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name (CamelCase to snake_case)."""
        name = cls.__name__
        import re
        name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
        return name.lower()
    
    def dict(self) -> dict[str, Any]:
        """Convert model attributes to dictionary."""
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps (UTC)."""
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class UUIDMixin:
    """Mixin for UUID primary key compatible with both PostgreSQL and SQLite."""
    
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft deletion (logical deletion)."""
    
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.deleted_at = None


__all__ = ["Base", "TimestampMixin", "UUIDMixin", "SoftDeleteMixin", "GUID", "SpatialGeometry"]
