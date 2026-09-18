"""Workload-related API endpoints."""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.api.dependencies import get_workload_service, optional_api_key_dependency
from app.core.logging import get_logger
from app.domain.models.workload import Workload

logger = get_logger(__name__)
router = APIRouter(dependencies=[Depends(optional_api_key_dependency)])


@router.get("/workloads")
async def list_workloads(
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    workload_service: WorkloadService = Depends(get_workload_service),
) -> dict[str, list[Workload]]:
    """List all discovered workloads."""
    logger.info("Listing workloads", namespace=namespace)
    workloads = await workload_service.get_workloads()

    if namespace:
        workloads = [w for w in workloads if w.namespace == namespace]

    return {"workloads": workloads}


@router.get("/workloads/{name}")
async def get_workload(
    name: str,
    namespace: str = Query(..., description="Namespace of the workload"),
    workload_service: WorkloadService = Depends(get_workload_service),
) -> Workload:
    """Get details for a specific workload."""
    logger.info("Getting workload", workload=name, namespace=namespace)
    return await workload_service.get_workload(name, namespace)


@router.get("/namespaces")
async def list_namespaces(
    workload_service: WorkloadService = Depends(get_workload_service),
) -> dict[str, list[str]]:
    """List all namespaces."""
    logger.info("Listing namespaces")
    workloads = await workload_service.get_workloads()
    namespaces = list(set(w.namespace for w in workloads))
    return {"namespaces": sorted(namespaces)}


@router.get("/pods")
async def list_pods(
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    workload_service: WorkloadService = Depends(get_workload_service),
) -> dict[str, list[dict]]:
    """List all pods (workload-based view)."""
    logger.info("Listing pods", namespace=namespace)
    workloads = await workload_service.get_workloads()

    if namespace:
        workloads = [w for w in workloads if w.namespace == namespace]

    # Return workload information as pod-like structure
    pods = [
        {
            "name": w.name,
            "namespace": w.namespace,
            "ready": w.available_replicas >= w.desired_replicas,
            "restart_count": w.restart_count,
            "health": w.health.value,
        }
        for w in workloads
    ]

    return {"pods": pods}
