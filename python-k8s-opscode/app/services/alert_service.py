"""Alert service for alert management."""

from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.domain.models.alert import Alert
from app.database.connection import get_db_session
from app.database.models import AlertModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class AlertService:
    """Service for alert operations."""

    async def create_alert(self, alert: Alert) -> Alert:
        """Create a new alert."""
        async with get_db_session() as session:
            db_alert = AlertModel(
                workload=alert.workload,
                namespace=alert.namespace,
                severity=alert.severity.value,
                title=alert.title,
                message=alert.message,
                metric_name=alert.metric_name,
                threshold=alert.threshold,
                current_value=alert.current_value,
                triggered_at=alert.triggered_at,
                is_resolved=alert.is_resolved,
                metadata=alert.metadata,
            )
            session.add(db_alert)
            await session.commit()
            await session.refresh(db_alert)

            alert.id = db_alert.id
            logger.info("Alert created", id=alert.id, workload=alert.workload)

            return alert

    async def get_alert(self, alert_id: str) -> Alert:
        """Get specific alert."""
        async with get_db_session() as session:
            result = await session.execute(
                select(AlertModel).where(AlertModel.id == alert_id)
            )
            db_alert = result.scalar_one_or_none()

            if not db_alert:
                raise ValueError(f"Alert {alert_id} not found")

            return self._db_to_domain(db_alert)

    async def list_alerts(
        self,
        is_resolved: bool | None = None,
        severity: str | None = None,
        workload: str | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """List alerts with optional filters."""
        async with get_db_session() as session:
            query = select(AlertModel)

            if is_resolved is not None:
                query = query.where(AlertModel.is_resolved == is_resolved)
            if severity:
                query = query.where(AlertModel.severity == severity)
            if workload:
                query = query.where(AlertModel.workload == workload)

            query = query.order_by(AlertModel.triggered_at.desc()).limit(limit)

            result = await session.execute(query)
            db_alerts = result.scalars().all()

            return [self._db_to_domain(alert) for alert in db_alerts]

    async def resolve_alert(self, alert_id: str) -> Alert:
        """Resolve an alert."""
        async with get_db_session() as session:
            result = await session.execute(
                select(AlertModel).where(AlertModel.id == alert_id)
            )
            db_alert = result.scalar_one_or_none()

            if not db_alert:
                raise ValueError(f"Alert {alert_id} not found")

            db_alert.is_resolved = True
            db_alert.resolved_at = datetime.utcnow()
            await session.commit()
            await session.refresh(db_alert)

            logger.info("Alert resolved", alert_id=alert_id)
            return self._db_to_domain(db_alert)

    def _db_to_domain(self, db_alert: AlertModel) -> Alert:
        """Convert database model to domain model."""
        from app.domain.enums.incident_severity import IncidentSeverity

        return Alert(
            id=db_alert.id,
            workload=db_alert.workload,
            namespace=db_alert.namespace,
            severity=IncidentSeverity(db_alert.severity),
            title=db_alert.title,
            message=db_alert.message,
            metric_name=db_alert.metric_name,
            threshold=db_alert.threshold,
            current_value=db_alert.current_value,
            triggered_at=db_alert.triggered_at,
            resolved_at=db_alert.resolved_at,
            is_resolved=db_alert.is_resolved,
            metadata=db_alert.metadata,
        )
