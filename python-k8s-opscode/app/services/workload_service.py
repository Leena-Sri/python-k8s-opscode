"""Workload service for business logic."""

from typing import Any

from app.core.logging import get_logger
from app.domain.models.workload import Workload
from app.domain.exceptions import WorkloadNotFoundError
from app.kubernetes.workload_manager import WorkloadManager
from app.cache.redis import RedisCache, workload_key
from app.database.connection import get_db_session
from app.database.models import WorkloadModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class WorkloadService:
    """Service for workload operations."""

    def __init__(self, workload_manager: WorkloadManager, cache: RedisCache):
        """Initialize workload service."""
        self._workload_manager = workload_manager
        self._cache = cache

    async def get_workloads(self, use_cache: bool = True) -> list[Workload]:
        """Get all workloads, optionally from cache."""
        if use_cache:
            cached = await self._cache.get("workloads:all")
            if cached:
                logger.debug("Workloads retrieved from cache")
                return [Workload(**w) for w in cached]

        workloads = await self._workload_manager.discover_workloads()

        if use_cache:
            await self._cache.set(
                "workloads:all",
                [w.model_dump() for w in workloads],
                ttl=60,  # Cache for 1 minute
            )

        return workloads

    async def get_workload(self, name: str, namespace: str, use_cache: bool = True) -> Workload:
        """Get specific workload, optionally from cache."""
        cache_key = workload_key(namespace, name)

        if use_cache:
            cached = await self._cache.get(cache_key)
            if cached:
                logger.debug("Workload retrieved from cache", name=name, namespace=namespace)
                return Workload(**cached)

        workload = await self._workload_manager.get_workload(name, namespace)
        if not workload:
            raise WorkloadNotFoundError(f"Workload {name} not found in namespace {namespace}")

        if use_cache:
            await self._cache.set(cache_key, workload.model_dump(), ttl=60)

        return workload

    async def persist_workload(self, workload: Workload) -> None:
        """Persist workload to database."""
        async with get_db_session() as session:
            # Check if workload exists
            result = await session.execute(
                select(WorkloadModel).where(
                    WorkloadModel.name == workload.name,
                    WorkloadModel.namespace == workload.namespace,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing workload
                existing.desired_replicas = workload.desired_replicas
                existing.available_replicas = workload.available_replicas
                existing.health = workload.health.value
                existing.restart_count = workload.restart_count
                existing.cpu_usage_percent = workload.cpu_usage_percent
                existing.memory_usage_percent = workload.memory_usage_percent
                existing.error_rate = workload.error_rate
                existing.response_latency_ms = workload.response_latency_ms
                existing.labels = workload.labels
                existing.annotations = workload.annotations
                existing.metadata = workload.metadata
                existing.updated_at = workload.updated_at
            else:
                # Create new workload
                db_workload = WorkloadModel(
                    name=workload.name,
                    namespace=workload.namespace,
                    kind=workload.kind,
                    desired_replicas=workload.desired_replicas,
                    available_replicas=workload.available_replicas,
                    health=workload.health.value,
                    restart_count=workload.restart_count,
                    cpu_usage_percent=workload.cpu_usage_percent,
                    memory_usage_percent=workload.memory_usage_percent,
                    error_rate=workload.error_rate,
                    response_latency_ms=workload.response_latency_ms,
                    labels=workload.labels,
                    annotations=workload.annotations,
                    metadata=workload.metadata,
                )
                session.add(db_workload)

            await session.commit()
            logger.info("Workload persisted", name=workload.name, namespace=workload.namespace)

    async def invalidate_cache(self, name: str | None = None, namespace: str | None = None) -> None:
        """Invalidate workload cache."""
        if name and namespace:
            cache_key = workload_key(namespace, name)
            await self._cache.delete(cache_key)
            logger.debug("Workload cache invalidated", name=name, namespace=namespace)
        else:
            await self._cache.delete("workloads:all")
            logger.debug("All workloads cache invalidated")
