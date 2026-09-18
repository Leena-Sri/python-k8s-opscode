"""Incident service for incident management."""

from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.domain.models.incident import Incident
from app.domain.exceptions import IncidentNotFoundError
from app.database.connection import get_db_session
from app.database.models import IncidentModel
from app.cache.redis import RedisCache, incident_key
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class IncidentService:
    """Service for incident operations."""

    def __init__(self, cache: RedisCache):
        """Initialize incident service."""
        self._cache = cache

    async def create_incident(self, incident: Incident) -> Incident:
        """Create a new incident."""
        async with get_db_session() as session:
            # Check if similar open incident already exists
            result = await session.execute(
                select(IncidentModel).where(
                    IncidentModel.workload == incident.workload,
                    IncidentModel.namespace == incident.namespace,
                    IncidentModel.type == incident.type.value,
                    IncidentModel.status == "OPEN",
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(
                    "Similar open incident already exists",
                    workload=incident.workload,
                    type=incident.type.value,
                    existing_id=existing.id,
                )
                return Incident(
                    id=existing.id,
                    workload=existing.workload,
                    namespace=existing.namespace,
                    severity=existing.severity,
                    type=existing.type,
                    description=existing.description,
                    detected_at=existing.detected_at,
                    acknowledged_at=existing.acknowledged_at,
                    resolved_at=existing.resolved_at,
                    status=existing.status,
                    metadata=existing.metadata,
                    resolution_notes=existing.resolution_notes,
                )

            # Create new incident
            db_incident = IncidentModel(
                workload=incident.workload,
                namespace=incident.namespace,
                severity=incident.severity.value,
                type=incident.type.value,
                description=incident.description,
                detected_at=incident.detected_at,
                status=incident.status.value,
                metadata=incident.metadata,
            )
            session.add(db_incident)
            await session.commit()
            await session.refresh(db_incident)

            incident.id = db_incident.id
            logger.info("Incident created", id=incident.id, workload=incident.workload, type=incident.type.value)

            # Invalidate cache
            await self._cache.delete("incidents:all")

            return incident

    async def get_incident(self, incident_id: str) -> Incident:
        """Get specific incident."""
        cache_key = incident_key(incident_id)
        cached = await self._cache.get(cache_key)
        if cached:
            logger.debug("Incident retrieved from cache", incident_id=incident_id)
            return Incident(**cached)

        async with get_db_session() as session:
            result = await session.execute(
                select(IncidentModel).where(IncidentModel.id == incident_id)
            )
            db_incident = result.scalar_one_or_none()

            if not db_incident:
                raise IncidentNotFoundError(f"Incident {incident_id} not found")

            incident = self._db_to_domain(db_incident)
            await self._cache.set(cache_key, incident.model_dump(), ttl=300)

            return incident

    async def list_incidents(
        self,
        status: str | None = None,
        severity: str | None = None,
        workload: str | None = None,
        limit: int = 100,
    ) -> list[Incident]:
        """List incidents with optional filters."""
        async with get_db_session() as session:
            query = select(IncidentModel)

            if status:
                query = query.where(IncidentModel.status == status)
            if severity:
                query = query.where(IncidentModel.severity == severity)
            if workload:
                query = query.where(IncidentModel.workload == workload)

            query = query.order_by(IncidentModel.detected_at.desc()).limit(limit)

            result = await session.execute(query)
            db_incidents = result.scalars().all()

            return [self._db_to_domain(inc) for inc in db_incidents]

    async def acknowledge_incident(self, incident_id: str) -> Incident:
        """Acknowledge an incident."""
        async with get_db_session() as session:
            result = await session.execute(
                select(IncidentModel).where(IncidentModel.id == incident_id)
            )
            db_incident = result.scalar_one_or_none()

            if not db_incident:
                raise IncidentNotFoundError(f"Incident {incident_id} not found")

            db_incident.status = "ACKNOWLEDGED"
            db_incident.acknowledged_at = datetime.utcnow()
            await session.commit()
            await session.refresh(db_incident)

            incident = self._db_to_domain(db_incident)

            # Invalidate cache
            await self._cache.delete(incident_key(incident_id))
            await self._cache.delete("incidents:all")

            logger.info("Incident acknowledged", incident_id=incident_id)
            return incident

    async def resolve_incident(self, incident_id: str, resolution_notes: str | None = None) -> Incident:
        """Resolve an incident."""
        async with get_db_session() as session:
            result = await session.execute(
                select(IncidentModel).where(IncidentModel.id == incident_id)
            )
            db_incident = result.scalar_one_or_none()

            if not db_incident:
                raise IncidentNotFoundError(f"Incident {incident_id} not found")

            db_incident.status = "RESOLVED"
            db_incident.resolved_at = datetime.utcnow()
            if resolution_notes:
                db_incident.resolution_notes = resolution_notes
            await session.commit()
            await session.refresh(db_incident)

            incident = self._db_to_domain(db_incident)

            # Invalidate cache
            await self._cache.delete(incident_key(incident_id))
            await self._cache.delete("incidents:all")

            logger.info("Incident resolved", incident_id=incident_id)
            return incident

    def _db_to_domain(self, db_incident: IncidentModel) -> Incident:
        """Convert database model to domain model."""
        from app.domain.enums.incident_severity import IncidentSeverity
        from app.domain.enums.incident_status import IncidentStatus
        from app.domain.enums.incident_type import IncidentType

        return Incident(
            id=db_incident.id,
            workload=db_incident.workload,
            namespace=db_incident.namespace,
            severity=IncidentSeverity(db_incident.severity),
            type=IncidentType(db_incident.type),
            description=db_incident.description,
            detected_at=db_incident.detected_at,
            acknowledged_at=db_incident.acknowledged_at,
            resolved_at=db_incident.resolved_at,
            status=IncidentStatus(db_incident.status),
            metadata=db_incident.metadata,
            resolution_notes=db_incident.resolution_notes,
        )
