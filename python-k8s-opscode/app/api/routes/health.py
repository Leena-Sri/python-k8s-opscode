"""Health check endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    status: str
    checks: dict[str, str]


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    from app.core.config import get_settings

    settings = get_settings()
    logger.debug("Health check requested")
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Readiness check endpoint."""
    logger.debug("Readiness check requested")
    # TODO: Add actual checks for database, Redis, Kubernetes
    return ReadinessResponse(
        status="ready",
        checks={
            "database": "ok",
            "redis": "ok",
            "kubernetes": "ok",
        },
    )


@router.get("/live", response_model=HealthResponse)
async def liveness_check() -> HealthResponse:
    """Liveness check endpoint."""
    logger.debug("Liveness check requested")
    from app.core.config import get_settings

    settings = get_settings()
    return HealthResponse(
        status="alive",
        version=settings.app_version,
        environment=settings.environment,
    )
