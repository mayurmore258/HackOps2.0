"""
THERMOS AI - Integrated Urban Heat, Industrial & Vehicular Pollution Intelligence Platform

FastAPI Application Entry Point.
"""

import time
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import ThermosBaseException
from app.core.logging import get_logger, setup_logging
from app.api.router import api_router

# Initialize structured logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown."""
    logger.info(
        "Application starting up",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database_url=settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
    )
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "THERMOS AI - Integrated Urban Heat, Industrial & Vehicular Pollution Intelligence Platform. "
        "Transforms fragmented environmental observations, satellite columns, vehicular emissions and "
        "regulatory compliance benchmarks into unified, explainable decision support."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pure ASGI Middleware for Request ID & Response Timing (zero deadlock, highly efficient)
class RequestTimingMiddleware:
    """Pure ASGI middleware that stamps X-Request-ID and X-Response-Time-MS."""
    def __init__(self, asgi_app):
        self.app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", req_id.encode("utf-8")))
                headers.append((b"x-response-time-ms", str(duration_ms).encode("utf-8")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.add_middleware(RequestTimingMiddleware)


# Global Exception Handlers
@app.exception_handler(ThermosBaseException)
async def thermos_exception_handler(request: Request, exc: ThermosBaseException):
    logger.warning(
        "Domain exception occurred",
        code=exc.code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": request.url.path,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        errors.append({
            "loc": [str(x) for x in err.get("loc", [])],
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": {"errors": errors},
            },
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": request.url.path,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception", error=str(exc), exc_info=True, path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "details": {"error_type": type(exc).__name__} if settings.DEBUG else {},
            },
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": request.url.path,
            }
        },
    )


# Health Endpoints
@app.get("/health", tags=["System Health"])
def root_health():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/health", tags=["System Health"])
def api_v1_health():
    """API v1 health and system status check endpoint."""
    from app.db.session import engine
    from sqlalchemy import text
    
    db_status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"unreachable: {str(e)}"
        
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status,
        "pilot_region": settings.PILOT_REGION,
        "demo_mode": settings.ENABLE_DEMO_MODE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Include API v1 router
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
