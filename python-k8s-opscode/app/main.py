"""Main application entry point for Opscode Platform."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from structlog import get_logger

from app.api.routes import (
    alerts,
    health,
    incidents,
    metrics,
    remediation,
    workloads,
)
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.connection import init_db, close_db
from app.cache.redis import init_redis, close_redis
from app.monitoring.prometheus import init_metrics
from app.services.monitoring_service import MonitoringService

# Configure logging
configure_logging()
logger = get_logger(__name__)
settings = get_settings()

# Global monitoring service
monitoring_service: MonitoringService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Opscode Platform", version=settings.app_version, environment=settings.environment)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized")

    # Initialize Prometheus metrics
    init_metrics()
    logger.info("Prometheus metrics initialized")

    # Start background monitoring service
    global monitoring_service

    # Initialize services
    from app.cache.redis import RedisCache
    from app.kubernetes.client import get_kubernetes_client
    from app.kubernetes.workload_manager import WorkloadManager
    from app.services.workload_service import WorkloadService
    from app.services.incident_service import IncidentService
    from app.services.remediation_service import RemediationService

    cache = RedisCache()
    k8s_client = get_kubernetes_client(use_mock=settings.is_development)
    workload_manager = WorkloadManager(k8s_client)
    workload_service = WorkloadService(workload_manager, cache)
    incident_service = IncidentService(cache)
    remediation_service = RemediationService(workload_manager, cache)

    monitoring_service = MonitoringService(workload_service, cache)
    monitoring_service.set_incident_service(incident_service)
    await monitoring_service.start()
    logger.info("Monitoring service started")

    yield

    # Shutdown
    logger.info("Shutting down Opscode Platform")

    if monitoring_service:
        await monitoring_service.stop()
        logger.info("Monitoring service stopped")

    await close_db()
    logger.info("Database connection closed")

    await close_redis()
    logger.info("Redis connection closed")

    logger.info("Opscode Platform shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Kubernetes Operations Platform - Automated monitoring, incident detection, and remediation",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(workloads.router, prefix=settings.api_prefix, tags=["Workloads"])
    app.include_router(incidents.router, prefix=settings.api_prefix, tags=["Incidents"])
    app.include_router(alerts.router, prefix=settings.api_prefix, tags=["Alerts"])
    app.include_router(remediation.router, prefix=settings.api_prefix, tags=["Remediation"])
    app.include_router(metrics.router, prefix=settings.api_prefix, tags=["Metrics"])

    # Prometheus metrics endpoint
    if settings.prometheus_enabled:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error", path=request.url.path, errors=exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation error", "errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
