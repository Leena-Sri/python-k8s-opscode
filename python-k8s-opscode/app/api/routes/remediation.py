"""Remediation-related API endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from pydantic import BaseModel

from app.api.dependencies import get_remediation_service, optional_api_key_dependency
from app.core.logging import get_logger
from app.domain.models.remediation_action import RemediationAction

logger = get_logger(__name__)
router = APIRouter(dependencies=[Depends(optional_api_key_dependency)])


class ScaleWorkloadRequest(BaseModel):
    """Request model for scaling a workload."""

    replicas: int = Query(..., ge=1, le=10, description="Number of replicas")


@router.get("/remediation/actions")
async def list_remediation_actions(
    workload: Optional[str] = Query(None, description="Filter by workload"),
    action_status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    remediation_service: RemediationService = Depends(get_remediation_service),
) -> dict[str, list[RemediationAction]]:
    """List all remediation actions."""
    logger.info("Listing remediation actions", workload=workload, status=action_status)
    actions = await remediation_service.list_remediation_actions(
        workload=workload,
        status=action_status,
        limit=limit,
    )
    return {"actions": actions}


@router.post("/remediation/{workload}/restart")
async def restart_workload(
    workload: str,
    namespace: str = Query(..., description="Namespace of the workload"),
    remediation_service: RemediationService = Depends(get_remediation_service),
) -> RemediationAction:
    """Restart a workload."""
    logger.info("Restarting workload", workload=workload, namespace=namespace)

    # Create remediation action
    from app.domain.enums.remediation_action import RemediationAction as RemediationActionEnum
    from app.domain.models.remediation_action import RemediationAction

    remediation = RemediationAction(
        workload=workload,
        namespace=namespace,
        action=RemediationActionEnum.RESTART,
        dry_run=True,  # API-triggered actions default to dry run
    )

    try:
        result = await remediation_service.execute_remediation(remediation)
        return result
    except Exception as e:
        logger.error("Failed to restart workload", workload=workload, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart workload: {e}",
        )


@router.post("/remediation/{workload}/scale")
async def scale_workload(
    workload: str,
    namespace: str = Query(..., description="Namespace of the workload"),
    replicas: int = Query(..., ge=1, le=10, description="Number of replicas"),
    remediation_service: RemediationService = Depends(get_remediation_service),
) -> RemediationAction:
    """Scale a workload."""
    logger.info("Scaling workload", workload=workload, namespace=namespace, replicas=replicas)

    # Create remediation action
    from app.domain.enums.remediation_action import RemediationAction as RemediationActionEnum
    from app.domain.models.remediation_action import RemediationAction

    remediation = RemediationAction(
        workload=workload,
        namespace=namespace,
        action=RemediationActionEnum.SCALE,
        dry_run=True,  # API-triggered actions default to dry run
        metadata={"target_replicas": replicas},
    )

    try:
        result = await remediation_service.execute_remediation(remediation)
        return result
    except Exception as e:
        logger.error("Failed to scale workload", workload=workload, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scale workload: {e}",
        )
