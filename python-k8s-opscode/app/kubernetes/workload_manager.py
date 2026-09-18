"""Workload manager for Kubernetes operations."""

from typing import Any

from app.core.logging import get_logger
from app.domain.models.workload import Workload
from app.domain.enums.health_status import HealthStatus
from app.kubernetes.client import KubernetesClientInterface

logger = get_logger(__name__)


class WorkloadManager:
    """Manager for Kubernetes workload operations."""

    def __init__(self, k8s_client: KubernetesClientInterface):
        """Initialize workload manager."""
        self._k8s_client = k8s_client

    async def discover_workloads(self) -> list[Workload]:
        """Discover all workloads across namespaces."""
        logger.info("Discovering workloads")
        workloads = []

        try:
            namespaces = await self._k8s_client.list_namespaces()
            for ns in namespaces:
                namespace = ns["name"]
                deployments = await self._k8s_client.list_deployments(namespace)

                for deploy in deployments:
                    workload = self._deployment_to_workload(deploy)
                    # Enhance with pod information
                    pods = await self._k8s_client.list_pods(namespace)
                    workload_pod_pods = [p for p in pods if workload.name in p["name"]]

                    if workload_pod_pods:
                        total_restarts = sum(p.get("restart_count", 0) for p in workload_pod_pods)
                        workload.restart_count = total_restarts

                        # Check for CrashLoopBackOff pods
                        crash_loops = [p for p in workload_pod_pods if p.get("phase") == "CrashLoopBackOff"]
                        if crash_loops:
                            workload.health = HealthStatus.UNHEALTHY
                        elif workload.available_replicas < workload.desired_replicas:
                            workload.health = HealthStatus.DEGRADED
                        else:
                            workload.health = HealthStatus.HEALTHY

                    workloads.append(workload)

            logger.info("Workloads discovered", count=len(workloads))
            return workloads

        except Exception as e:
            logger.error("Failed to discover workloads", error=str(e))
            raise

    async def get_workload(self, name: str, namespace: str) -> Workload | None:
        """Get specific workload."""
        logger.info("Getting workload", name=name, namespace=namespace)
        try:
            deployment = await self._k8s_client.get_deployment(name, namespace)
            if not deployment:
                return None

            workload = self._deployment_to_workload(deployment)

            # Get pod information
            pods = await self._k8s_client.list_pods(namespace)
            workload_pods = [p for p in pods if name in p["name"]]

            if workload_pods:
                total_restarts = sum(p.get("restart_count", 0) for p in workload_pods)
                workload.restart_count = total_restarts

                # Check health
                crash_loops = [p for p in workload_pods if p.get("phase") == "CrashLoopBackOff"]
                if crash_loops:
                    workload.health = HealthStatus.UNHEALTHY
                elif workload.available_replicas < workload.desired_replicas:
                    workload.health = HealthStatus.DEGRADED
                else:
                    workload.health = HealthStatus.HEALTHY

            return workload

        except Exception as e:
            logger.error("Failed to get workload", name=name, namespace=namespace, error=str(e))
            raise

    async def restart_workload(self, name: str, namespace: str) -> bool:
        """Restart a workload."""
        logger.info("Restarting workload", name=name, namespace=namespace)
        try:
            return await self._k8s_client.restart_deployment(name, namespace)
        except Exception as e:
            logger.error("Failed to restart workload", name=name, namespace=namespace, error=str(e))
            raise

    async def scale_workload(self, name: str, namespace: str, replicas: int) -> bool:
        """Scale a workload."""
        logger.info("Scaling workload", name=name, namespace=namespace, replicas=replicas)
        try:
            return await self._k8s_client.scale_deployment(name, namespace, replicas)
        except Exception as e:
            logger.error("Failed to scale workload", name=name, namespace=namespace, error=str(e))
            raise

    def _deployment_to_workload(self, deployment: dict[str, Any]) -> Workload:
        """Convert deployment dict to Workload model."""
        return Workload(
            name=deployment["name"],
            namespace=deployment["namespace"],
            kind="Deployment",
            desired_replicas=deployment["replicas"],
            available_replicas=deployment["available_replicas"],
            labels=deployment.get("labels", {}),
            annotations=deployment.get("annotations", {}),
            metadata={
                "ready_replicas": deployment.get("ready_replicas", 0),
                "updated_replicas": deployment.get("updated_replicas", 0),
                "created_at": deployment.get("created_at"),
            },
        )
