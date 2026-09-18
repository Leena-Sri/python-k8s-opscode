"""Monitoring service for health checks and incident detection."""

import asyncio
from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.models.workload import Workload
from app.domain.models.incident import Incident
from app.domain.enums.incident_severity import IncidentSeverity
from app.domain.enums.incident_status import IncidentStatus
from app.domain.enums.incident_type import IncidentType
from app.domain.enums.health_status import HealthStatus
from app.services.workload_service import WorkloadService

from app.cache.redis import RedisCache, health_check_key

logger = get_logger(__name__)
settings = get_settings()


class MonitoringService:
    """Service for periodic monitoring and health checks."""

    def __init__(
        self,
        workload_service: WorkloadService,
        cache: RedisCache,
    ):
        """Initialize monitoring service."""
        self._workload_service = workload_service
        self._cache = cache
        self._incident_service = None  # Set later to avoid circular import

    def set_incident_service(self, incident_service) -> None:
        """Set incident service (called after initialization to avoid circular import)."""
        self._incident_service = incident_service
        self._scheduler = AsyncIOScheduler()
        self._running = False

    async def start(self) -> None:
        """Start monitoring service."""
        if self._running:
            logger.warning("Monitoring service already running")
            return

        logger.info("Starting monitoring service")

        # Schedule periodic tasks
        self._scheduler.add_job(
            self._discovery_job,
            "interval",
            seconds=settings.workload_discovery_interval,
            id="workload_discovery",
        )

        self._scheduler.add_job(
            self._health_check_job,
            "interval",
            seconds=settings.health_check_interval,
            id="health_checks",
        )

        self._scheduler.add_job(
            self._incident_check_job,
            "interval",
            seconds=settings.incident_check_interval,
            id="incident_detection",
        )

        self._scheduler.start()
        self._running = True
        logger.info("Monitoring service started")

    async def stop(self) -> None:
        """Stop monitoring service."""
        if not self._running:
            return

        logger.info("Stopping monitoring service")
        self._scheduler.shutdown()
        self._running = False
        logger.info("Monitoring service stopped")

    async def _discovery_job(self) -> None:
        """Periodic workload discovery job."""
        try:
            logger.debug("Running workload discovery")
            workloads = await self._workload_service.get_workloads(use_cache=False)

            for workload in workloads:
                await self._workload_service.persist_workload(workload)

            logger.info("Workload discovery completed", count=len(workloads))
        except Exception as e:
            logger.error("Workload discovery failed", error=str(e))

    async def _health_check_job(self) -> None:
        """Periodic health check job."""
        try:
            logger.debug("Running health checks")
            workloads = await self._workload_service.get_workloads()

            for workload in workloads:
                health_result = await self._evaluate_workload_health(workload)

                # Cache health check result
                cache_key = health_check_key(workload.namespace, workload.name)
                await self._cache.set(cache_key, health_result, ttl=300)

                # Update workload with health information
                workload.cpu_usage_percent = health_result.get("cpu_usage", 0.0)
                workload.memory_usage_percent = health_result.get("memory_usage", 0.0)
                workload.error_rate = health_result.get("error_rate", 0.0)
                workload.response_latency_ms = health_result.get("latency_ms", 0.0)

                await self._workload_service.persist_workload(workload)

            logger.info("Health checks completed", count=len(workloads))
        except Exception as e:
            logger.error("Health checks failed", error=str(e))

    async def _incident_check_job(self) -> None:
        """Periodic incident detection job."""
        try:
            logger.debug("Running incident detection")
            workloads = await self._workload_service.get_workloads()

            for workload in workloads:
                incidents = await self._detect_incidents(workload)
                # Incident service will be set separately
                if self._incident_service:
                    for incident in incidents:
                        await self._incident_service.create_incident(incident)

            logger.info("Incident detection completed", workloads_checked=len(workloads))
        except Exception as e:
            logger.error("Incident detection failed", error=str(e))

    async def _evaluate_workload_health(self, workload: Workload) -> dict[str, Any]:
        """Evaluate health of a workload."""
        health_result = {
            "workload": workload.name,
            "namespace": workload.namespace,
            "healthy": True,
            "checks": [],
        }

        # Check replica availability
        replica_check = {
            "type": "replica_availability",
            "passed": workload.available_replicas >= workload.desired_replicas,
            "value": workload.available_replicas,
            "threshold": workload.desired_replicas,
        }
        health_result["checks"].append(replica_check)

        if not replica_check["passed"]:
            health_result["healthy"] = False

        # Check restart count
        restart_check = {
            "type": "restart_count",
            "passed": workload.restart_count < settings.restart_threshold,
            "value": workload.restart_count,
            "threshold": settings.restart_threshold,
        }
        health_result["checks"].append(restart_check)

        if not restart_check["passed"]:
            health_result["healthy"] = False

        # Check health status
        health_status_check = {
            "type": "health_status",
            "passed": workload.health in [HealthStatus.HEALTHY, HealthStatus.DEGRADED],
            "value": workload.health.value,
            "threshold": "HEALTHY",
        }
        health_result["checks"].append(health_status_check)

        if not health_status_check["passed"]:
            health_result["healthy"] = False

        # Simulate CPU and memory metrics (in production, these would come from Prometheus)
        cpu_usage = 0.0
        memory_usage = 0.0

        if workload.health == HealthStatus.UNHEALTHY:
            cpu_usage = 95.0
            memory_usage = 90.0
        elif workload.health == HealthStatus.DEGRADED:
            cpu_usage = 75.0
            memory_usage = 80.0
        else:
            cpu_usage = 45.0
            memory_usage = 50.0

        cpu_check = {
            "type": "cpu_usage",
            "passed": cpu_usage < settings.cpu_threshold_percent,
            "value": cpu_usage,
            "threshold": settings.cpu_threshold_percent,
        }
        health_result["checks"].append(cpu_check)
        health_result["cpu_usage"] = cpu_usage

        if not cpu_check["passed"]:
            health_result["healthy"] = False

        memory_check = {
            "type": "memory_usage",
            "passed": memory_usage < settings.memory_threshold_percent,
            "value": memory_usage,
            "threshold": settings.memory_threshold_percent,
        }
        health_result["checks"].append(memory_check)
        health_result["memory_usage"] = memory_usage

        if not memory_check["passed"]:
            health_result["healthy"] = False

        return health_result

    async def _detect_incidents(self, workload: Workload) -> list[Incident]:
        """Detect incidents for a workload."""
        incidents = []

        # Check for CrashLoopBackOff
        if workload.health == HealthStatus.UNHEALTHY and workload.restart_count > settings.restart_threshold:
            incident = Incident(
                workload=workload.name,
                namespace=workload.namespace,
                severity=IncidentSeverity.CRITICAL,
                type=IncidentType.POD_CRASH_LOOP,
                description=f"Pods in CrashLoopBackOff with {workload.restart_count} restarts",
                metadata={"restart_count": workload.restart_count},
            )
            incidents.append(incident)

        # Check for replica shortage
        if workload.available_replicas < workload.desired_replicas - settings.replica_shortage_threshold:
            incident = Incident(
                workload=workload.name,
                namespace=workload.namespace,
                severity=IncidentSeverity.WARNING,
                type=IncidentType.REPLICA_SHORTAGE,
                description=f"Replica shortage: {workload.available_replicas}/{workload.desired_replicas} available",
                metadata={
                    "available": workload.available_replicas,
                    "desired": workload.desired_replicas,
                },
            )
            incidents.append(incident)

        # Check for high CPU
        if workload.cpu_usage_percent > settings.cpu_threshold_percent:
            incident = Incident(
                workload=workload.name,
                namespace=workload.namespace,
                severity=IncidentSeverity.WARNING,
                type=IncidentType.HIGH_CPU,
                description=f"High CPU usage: {workload.cpu_usage_percent:.1f}%",
                metadata={"cpu_usage": workload.cpu_usage_percent},
            )
            incidents.append(incident)

        # Check for high memory
        if workload.memory_usage_percent > settings.memory_threshold_percent:
            incident = Incident(
                workload=workload.name,
                namespace=workload.namespace,
                severity=IncidentSeverity.WARNING,
                type=IncidentType.HIGH_MEMORY,
                description=f"High memory usage: {workload.memory_usage_percent:.1f}%",
                metadata={"memory_usage": workload.memory_usage_percent},
            )
            incidents.append(incident)

        return incidents
