"""Incident-related API endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from pydantic import BaseModel

from app.api.dependencies import get_incident_service, optional_api_key_dependency
from app.core.logging import get_logger
from app.domain.models.incident import Incident

logger = get_logger(__name__)
router = APIRouter(dependencies=[Depends(optional_api_key_dependency)])


class ResolveIncidentRequest(BaseModel):
    """Request model for resolving an incident."""

    resolution_notes: Optional[str] = None


@router.get("/incidents")
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    workload: Optional[str] = Query(None, description="Filter by workload"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    incident_service: IncidentService = Depends(get_incident_service),
) -> dict[str, list[Incident]]:
    """List all incidents."""
    logger.info("Listing incidents", status=status, severity=severity, workload=workload)
    incidents = await incident_service.list_incidents(
        status=status,
        severity=severity,
        workload=workload,
        limit=limit,
    )
    return {"incidents": incidents}


@router.get("/incidents/{id}")
async def get_incident(
    id: str,
    incident_service: IncidentService = Depends(get_incident_service),
) -> Incident:
    """Get details for a specific incident."""
    logger.info("Getting incident", incident_id=id)
    try:
        return await incident_service.get_incident(id)
    except Exception as e:
        logger.error("Failed to get incident", incident_id=id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {id} not found",
        )


@router.post("/incidents/{id}/acknowledge")
async def acknowledge_incident(
    id: str,
    incident_service: IncidentService = Depends(get_incident_service),
) -> Incident:
    """Acknowledge an incident."""
    logger.info("Acknowledging incident", incident_id=id)
    try:
        return await incident_service.acknowledge_incident(id)
    except Exception as e:
        logger.error("Failed to acknowledge incident", incident_id=id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {id} not found",
        )


@router.post("/incidents/{id}/resolve")
async def resolve_incident(
    id: str,
    request: ResolveIncidentRequest,
    incident_service: IncidentService = Depends(get_incident_service),
) -> Incident:
    """Resolve an incident."""
    logger.info("Resolving incident", incident_id=id)
    try:
        return await incident_service.resolve_incident(id, request.resolution_notes)
    except Exception as e:
        logger.error("Failed to resolve incident", incident_id=id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {id} not found",
        )
