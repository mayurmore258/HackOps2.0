"""
THERMOS AI - Logging Configuration

Structured logging using structlog for consistent, machine-readable logs.
"""

import logging
import sys
from pathlib import Path
from typing import Any
import structlog
from structlog.typing import EventDict, WrappedLogger

from app.core.config import settings


def add_app_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application context to log events."""
    event_dict["app"] = settings.APP_NAME
    event_dict["environment"] = settings.APP_ENV
    event_dict["version"] = settings.APP_VERSION
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Ensure log directory exists
    log_file = Path(settings.LOG_FILE_PATH)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Configure structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.DEBUG:
        # Development: use console renderer with colors
        shared_processors.append(structlog.dev.ConsoleRenderer())
    else:
        # Production: use JSON renderer
        shared_processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library root logger to use structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer() if settings.DEBUG 
            else structlog.processors.JSONRenderer(),
        ],
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # File handler for production
    if not settings.DEBUG:
        file_handler = logging.FileHandler(settings.LOG_FILE_PATH)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
