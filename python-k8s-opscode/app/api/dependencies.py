"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.cache.redis import RedisCache, get_redis
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import verify_api_key
from app.database.connection import get_db_session
from app.kubernetes.client import get_kubernetes_client
from app.kubernetes.workload_manager import WorkloadManager
from app.services.workload_service import WorkloadService
from app.services.incident_service import IncidentService
from app.services.alert_service import AlertService
from app.services.remediation_service import RemediationService

logger = get_logger(__name__)
settings = get_settings()
security = HTTPBearer()


async def get_cache() -> AsyncGenerator[RedisCache, None]:
    """Get Redis cache instance."""
    cache = RedisCache()
    yield cache


async def get_workload_manager(
    cache: RedisCache = Depends(get_cache),
) -> AsyncGenerator[WorkloadManager, None]:
    """Get workload manager instance."""
    k8s_client = get_kubernetes_client(use_mock=settings.is_development)
    workload_manager = WorkloadManager(k8s_client)
    yield workload_manager


async def get_workload_service(
    workload_manager: WorkloadManager = Depends(get_workload_manager),
    cache: RedisCache = Depends(get_cache),
) -> AsyncGenerator[WorkloadService, None]:
    """Get workload service instance."""
    workload_service = WorkloadService(workload_manager, cache)
    yield workload_service


async def get_incident_service(
    cache: RedisCache = Depends(get_cache),
) -> AsyncGenerator[IncidentService, None]:
    """Get incident service instance."""
    incident_service = IncidentService(cache)
    yield incident_service


async def get_alert_service() -> AsyncGenerator[AlertService, None]:
    """Get alert service instance."""
    alert_service = AlertService()
    yield alert_service


async def get_remediation_service(
    workload_manager: WorkloadManager = Depends(get_workload_manager),
    cache: RedisCache = Depends(get_cache),
) -> AsyncGenerator[RemediationService, None]:
    """Get remediation service instance."""
    remediation_service = RemediationService(workload_manager, cache)
    yield remediation_service


async def verify_api_key_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    """Verify API key for authentication."""
    api_key = credentials.credentials

    # In production, this would check against a database or secret store
    # For now, we'll check against environment variable
    valid_keys = settings.secret_key.split(",") if "," in settings.secret_key else [settings.secret_key]

    if not verify_api_key(api_key, valid_keys):
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


async def optional_api_key_dependency(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> None:
    """Optional API key verification for public endpoints."""
    if credentials:
        api_key = credentials.credentials
        valid_keys = settings.secret_key.split(",") if "," in settings.secret_key else [settings.secret_key]
        if not verify_api_key(api_key, valid_keys):
            logger.warning("Invalid API key provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
