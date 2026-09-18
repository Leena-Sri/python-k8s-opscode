"""Metrics-related API endpoints."""

from fastapi import APIRouter, Depends
from typing import Optional

from app.api.dependencies import optional_api_key_dependency
from app.core.logging import get_logger
from app.database.connection import get_db_session
from app.database.models import WorkloadModel, IncidentModel, RemediationActionModel
from sqlalchemy import select, func

logger = get_logger(__name__)
router = APIRouter(dependencies=[Depends(optional_api_key_dependency)])


@router.get("/metrics/summary")
async def get_metrics_summary() -> dict[str, dict]:
    """Get metrics summary."""
    logger.info("Getting metrics summary")

    async with get_db_session() as session:
        # Get workload counts
        total_workloads = await session.execute(select(func.count(WorkloadModel.id)))
        healthy_workloads = await session.execute(
            select(func.count(WorkloadModel.id)).where(WorkloadModel.health == "HEALTHY")
        )
        degraded_workloads = await session.execute(
            select(func.count(WorkloadModel.id)).where(WorkloadModel.health == "DEGRADED")
        )
        unhealthy_workloads = await session.execute(
            select(func.count(WorkloadModel.id)).where(WorkloadModel.health == "UNHEALTHY")
        )

        # Get incident counts
        total_incidents = await session.execute(select(func.count(IncidentModel.id)))
        open_incidents = await session.execute(
            select(func.count(IncidentModel.id)).where(IncidentModel.status == "OPEN")
        )
        critical_incidents = await session.execute(
            select(func.count(IncidentModel.id)).where(
                IncidentModel.status == "OPEN",
                IncidentModel.severity == "CRITICAL"
            )
        )

        # Get remediation counts
        total_remediations = await session.execute(select(func.count(RemediationActionModel.id)))
        successful_remediations = await session.execute(
            select(func.count(RemediationActionModel.id)).where(RemediationActionModel.status == "SUCCESS")
        )
        failed_remediations = await session.execute(
            select(func.count(RemediationActionModel.id)).where(RemediationActionModel.status == "FAILED")
        )

        return {
            "workloads": {
                "total": total_workloads.scalar() or 0,
                "healthy": healthy_workloads.scalar() or 0,
                "degraded": degraded_workloads.scalar() or 0,
                "unhealthy": unhealthy_workloads.scalar() or 0,
            },
            "incidents": {
                "total": total_incidents.scalar() or 0,
                "open": open_incidents.scalar() or 0,
                "critical": critical_incidents.scalar() or 0,
            },
            "remediations": {
                "total": total_remediations.scalar() or 0,
                "successful": successful_remediations.scalar() or 0,
                "failed": failed_remediations.scalar() or 0,
            },
        }
