"""Alert-related API endpoints."""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.api.dependencies import get_alert_service, optional_api_key_dependency
from app.core.logging import get_logger
from app.domain.models.alert import Alert

logger = get_logger(__name__)
router = APIRouter(dependencies=[Depends(optional_api_key_dependency)])


@router.get("/alerts")
async def list_alerts(
    is_resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    workload: Optional[str] = Query(None, description="Filter by workload"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    alert_service: AlertService = Depends(get_alert_service),
) -> dict[str, list[Alert]]:
    """List all alerts."""
    logger.info("Listing alerts", is_resolved=is_resolved, severity=severity, workload=workload)
    alerts = await alert_service.list_alerts(
        is_resolved=is_resolved,
        severity=severity,
        workload=workload,
        limit=limit,
    )
    return {"alerts": alerts}
