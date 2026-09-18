"""Remediation service for automated remediation actions."""

import asyncio
from datetime import datetime
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.models.remediation_action import RemediationAction
from app.domain.models.incident import Incident
from app.domain.enums.remediation_action import RemediationAction as RemediationActionEnum
from app.domain.enums.remediation_status import RemediationStatus
from app.domain.exceptions import RemediationError
from app.database.connection import get_db_session
from app.database.models import RemediationActionModel
from app.cache.redis import RedisCache, DistributedLock, remediation_lock_key, cooldown_key
from app.kubernetes.workload_manager import WorkloadManager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)
settings = get_settings()


class RemediationService:
    """Service for remediation operations."""

    def __init__(
        self,
        workload_manager: WorkloadManager,
        cache: RedisCache,
    ):
        """Initialize remediation service."""
        self._workload_manager = workload_manager
        self._cache = cache
        self._lock = DistributedLock(cache._client)

    async def evaluate_remediation(self, incident: Incident) -> RemediationAction | None:
        """Evaluate if remediation should be performed for an incident."""
        if not settings.remediation_enabled:
            logger.info("Remediation disabled, skipping evaluation", incident_id=incident.id)
            return None

        # Check if namespace is allowed
        if incident.namespace not in settings.remediation_allowed_namespaces:
            logger.info(
                "Namespace not in allowed list",
                namespace=incident.namespace,
                incident_id=incident.id,
            )
            return None

        # Check if workload is in allowed list (if specified)
        if settings.remediation_allowed_workloads and incident.workload not in settings.remediation_allowed_workloads:
            logger.info(
                "Workload not in allowed list",
                workload=incident.workload,
                incident_id=incident.id,
            )
            return None

        # Check cooldown
        cooldown_key_str = cooldown_key(incident.workload, incident.namespace, incident.type.value)
        if await self._cache.exists(cooldown_key_str):
            logger.info(
                "Remediation in cooldown period",
                workload=incident.workload,
                incident_id=incident.id,
            )
            return None

        # Determine remediation action based on incident type
        action = self._determine_action(incident)
        if not action:
            logger.info("No remediation action determined", incident_id=incident.id)
            return None

        # Create remediation action
        remediation = RemediationAction(
            incident_id=incident.id,
            workload=incident.workload,
            namespace=incident.namespace,
            action=action,
            dry_run=settings.remediation_dry_run,
            metadata={"incident_type": incident.type.value},
        )

        return remediation

    async def execute_remediation(self, remediation: RemediationAction) -> RemediationAction:
        """Execute a remediation action."""
        logger.info(
            "Executing remediation",
            workload=remediation.workload,
            action=remediation.action.value,
            dry_run=remediation.dry_run,
        )

        # Acquire distributed lock
        lock_key = remediation_lock_key(remediation.workload, remediation.namespace)
        if not await self._lock.acquire(lock_key, ttl=60):
            logger.warning("Failed to acquire remediation lock", workload=remediation.workload)
            remediation.status = RemediationStatus.FAILED
            remediation.error_message = "Failed to acquire lock"
            await self._persist_remediation(remediation)
            return remediation

        try:
            remediation.status = RemediationStatus.IN_PROGRESS
            await self._persist_remediation(remediation)

            if remediation.dry_run:
                logger.info("Dry run mode, skipping actual remediation")
                result = await self._dry_run_remediation(remediation)
            else:
                result = await self._execute_remediation_action(remediation)

            if result:
                remediation.status = RemediationStatus.SUCCESS
                remediation.completed_at = datetime.utcnow()

                # Set cooldown
                cooldown_key_str = cooldown_key(
                    remediation.workload,
                    remediation.namespace,
                    remediation.action.value,
                )
                await self._cache.set(
                    cooldown_key_str,
                    "cooldown",
                    ttl=settings.remediation_cooldown_seconds,
                )

                logger.info(
                    "Remediation successful",
                    workload=remediation.workload,
                    action=remediation.action.value,
                )
            else:
                remediation.status = RemediationStatus.FAILED
                remediation.error_message = "Remediation action failed"
                remediation.completed_at = datetime.utcnow()
                logger.warning(
                    "Remediation failed",
                    workload=remediation.workload,
                    action=remediation.action.value,
                )

            await self._persist_remediation(remediation)
            return remediation

        except Exception as e:
            logger.error(
                "Remediation execution error",
                workload=remediation.workload,
                error=str(e),
            )
            remediation.status = RemediationStatus.FAILED
            remediation.error_message = str(e)
            remediation.completed_at = datetime.utcnow()
            await self._persist_remediation(remediation)
            raise RemediationError(f"Remediation failed: {e}")
        finally:
            await self._lock.release(lock_key)

    @retry(
        stop=stop_after_attempt(settings.remediation_max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _execute_remediation_action(self, remediation: RemediationAction) -> bool:
        """Execute the actual remediation action with retry logic."""
        if remediation.action == RemediationActionEnum.RESTART:
            return await self._workload_manager.restart_workload(
                remediation.workload,
                remediation.namespace,
            )
        elif remediation.action == RemediationActionEnum.SCALE:
            # Scale up by 1 replica
            # In production, this would be based on incident details
            return await self._workload_manager.scale_workload(
                remediation.workload,
                remediation.namespace,
                replicas=4,  # Example: scale to 4 replicas
            )
        elif remediation.action == RemediationActionEnum.ROLLOUT_RESTART:
            return await self._workload_manager.restart_workload(
                remediation.workload,
                remediation.namespace,
            )
        else:
            logger.warning("Unknown remediation action", action=remediation.action.value)
            return False

    async def _dry_run_remediation(self, remediation: RemediationAction) -> bool:
        """Simulate remediation in dry run mode."""
        logger.info(
            "Dry run remediation",
            workload=remediation.workload,
            action=remediation.action.value,
        )

        # Simulate delay
        await asyncio.sleep(1)

        # Simulate success
        return True

    async def _persist_remediation(self, remediation: RemediationAction) -> None:
        """Persist remediation action to database."""
        async with get_db_session() as session:
            if remediation.id:
                # Update existing
                result = await session.execute(
                    select(RemediationActionModel).where(RemediationActionModel.id == remediation.id)
                )
                db_remediation = result.scalar_one_or_none()

                if db_remediation:
                    db_remediation.status = remediation.status.value
                    db_remediation.completed_at = remediation.completed_at
                    db_remediation.error_message = remediation.error_message
                    db_remediation.retry_count = remediation.retry_count
                    db_remediation.metadata = remediation.metadata
            else:
                # Create new
                db_remediation = RemediationActionModel(
                    incident_id=remediation.incident_id,
                    workload=remediation.workload,
                    namespace=remediation.namespace,
                    action=remediation.action.value,
                    status=remediation.status.value,
                    dry_run=remediation.dry_run,
                    initiated_at=remediation.initiated_at,
                    completed_at=remediation.completed_at,
                    error_message=remediation.error_message,
                    retry_count=remediation.retry_count,
                    metadata=remediation.metadata,
                )
                session.add(db_remediation)
                remediation.id = db_remediation.id

            await session.commit()
            logger.info("Remediation persisted", id=remediation.id)

    async def list_remediation_actions(
        self,
        workload: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[RemediationAction]:
        """List remediation actions with optional filters."""
        async with get_db_session() as session:
            query = select(RemediationActionModel)

            if workload:
                query = query.where(RemediationActionModel.workload == workload)
            if status:
                query = query.where(RemediationActionModel.status == status)

            query = query.order_by(RemediationActionModel.initiated_at.desc()).limit(limit)

            result = await session.execute(query)
            db_remediations = result.scalars().all()

            return [self._db_to_domain(r) for r in db_remediations]

    def _determine_action(self, incident: Incident) -> RemediationActionEnum | None:
        """Determine appropriate remediation action based on incident type."""
        from app.domain.enums.incident_type import IncidentType

        if incident.type == IncidentType.POD_CRASH_LOOP:
            return RemediationActionEnum.RESTART
        elif incident.type == IncidentType.REPLICA_SHORTAGE:
            return RemediationActionEnum.SCALE
        elif incident.type == IncidentType.HIGH_CPU:
            return RemediationActionEnum.SCALE
        elif incident.type == IncidentType.HIGH_MEMORY:
            return RemediationActionEnum.SCALE
        else:
            return None

    def _db_to_domain(self, db_remediation: RemediationActionModel) -> RemediationAction:
        """Convert database model to domain model."""
        from app.domain.enums.remediation_action import RemediationAction
        from app.domain.enums.remediation_status import RemediationStatus

        return RemediationAction(
            id=db_remediation.id,
            incident_id=db_remediation.incident_id,
            workload=db_remediation.workload,
            namespace=db_remediation.namespace,
            action=RemediationAction(db_remediation.action),
            status=RemediationStatus(db_remediation.status),
            dry_run=db_remediation.dry_run,
            initiated_at=db_remediation.initiated_at,
            completed_at=db_remediation.completed_at,
            error_message=db_remediation.error_message,
            retry_count=db_remediation.retry_count,
            metadata=db_remediation.metadata,
        )
