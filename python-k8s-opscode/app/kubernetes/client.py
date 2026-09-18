"""Kubernetes client abstraction layer."""

from abc import ABC, abstractmethod
from typing import Any

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.exceptions import KubernetesConnectionError

logger = get_logger(__name__)
settings = get_settings()


class KubernetesClientInterface(ABC):
    """Abstract interface for Kubernetes client operations."""

    @abstractmethod
    async def list_namespaces(self) -> list[dict[str, Any]]:
        """List all namespaces."""
        pass

    @abstractmethod
    async def list_deployments(self, namespace: str) -> list[dict[str, Any]]:
        """List deployments in namespace."""
        pass

    @abstractmethod
    async def list_pods(self, namespace: str) -> list[dict[str, Any]]:
        """List pods in namespace."""
        pass

    @abstractmethod
    async def list_services(self, namespace: str) -> list[dict[str, Any]]:
        """List services in namespace."""
        pass

    @abstractmethod
    async def get_deployment(self, name: str, namespace: str) -> dict[str, Any] | None:
        """Get specific deployment."""
        pass

    @abstractmethod
    async def get_pod(self, name: str, namespace: str) -> dict[str, Any] | None:
        """Get specific pod."""
        pass

    @abstractmethod
    async def restart_deployment(self, name: str, namespace: str) -> bool:
        """Restart deployment via rollout restart."""
        pass

    @abstractmethod
    async def scale_deployment(self, name: str, namespace: str, replicas: int) -> bool:
        """Scale deployment to specific replica count."""
        pass

    @abstractmethod
    async def delete_pod(self, name: str, namespace: str) -> bool:
        """Delete a pod."""
        pass


class KubernetesClient(KubernetesClientInterface):
    """Real Kubernetes client implementation."""

    def __init__(self):
        """Initialize Kubernetes client."""
        self._apps_v1: client.AppsV1Api | None = None
        self._core_v1: client.CoreV1Api | None = None
        self._connected = False

    def _connect(self) -> None:
        """Establish connection to Kubernetes cluster."""
        if self._connected:
            return

        try:
            if settings.kubeconfig_path:
                config.load_kube_config(config_file=settings.kubeconfig_path)
            else:
                # Try in-cluster config first, then local config
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()

            self._apps_v1 = client.AppsV1Api()
            self._core_v1 = client.CoreV1Api()
            self._connected = True
            logger.info("Kubernetes client connected")
        except Exception as e:
            logger.error("Failed to connect to Kubernetes", error=str(e))
            raise KubernetesConnectionError(f"Failed to connect to Kubernetes: {e}")

    def _ensure_connected(self) -> None:
        """Ensure client is connected."""
        if not self._connected:
            self._connect()

    async def list_namespaces(self) -> list[dict[str, Any]]:
        """List all namespaces."""
        self._ensure_connected()
        try:
            response = self._core_v1.list_namespace(timeout_seconds=settings.kubernetes_timeout)
            return [
                {
                    "name": ns.metadata.name,
                    "labels": ns.metadata.labels or {},
                    "status": ns.status.phase,
                    "created_at": ns.metadata.creation_time.isoformat() if ns.metadata.creation_time else None,
                }
                for ns in response.items
            ]
        except ApiException as e:
            logger.error("Failed to list namespaces", error=str(e))
            raise KubernetesConnectionError(f"Failed to list namespaces: {e}")

    async def list_deployments(self, namespace: str) -> list[dict[str, Any]]:
        """List deployments in namespace."""
        self._ensure_connected()
        try:
            response = self._apps_v1.list_namespaced_deployment(
                namespace=namespace,
                timeout_seconds=settings.kubernetes_timeout,
            )
            return [
                {
                    "name": deploy.metadata.name,
                    "namespace": deploy.metadata.namespace,
                    "replicas": deploy.spec.replicas,
                    "available_replicas": deploy.status.available_replicas or 0,
                    "ready_replicas": deploy.status.ready_replicas or 0,
                    "updated_replicas": deploy.status.updated_replicas or 0,
                    "labels": deploy.metadata.labels or {},
                    "annotations": deploy.metadata.annotations or {},
                    "created_at": deploy.metadata.creation_time.isoformat() if deploy.metadata.creation_time else None,
                }
                for deploy in response.items
            ]
        except ApiException as e:
            logger.error("Failed to list deployments", namespace=namespace, error=str(e))
            raise KubernetesConnectionError(f"Failed to list deployments: {e}")

    async def list_pods(self, namespace: str) -> list[dict[str, Any]]:
        """List pods in namespace."""
        self._ensure_connected()
        try:
            response = self._core_v1.list_namespaced_pod(
                namespace=namespace,
                timeout_seconds=settings.kubernetes_timeout,
            )
            return [
                {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": pod.status.phase,
                    "ready": all(container.ready for container in (pod.status.container_statuses or [])),
                    "restart_count": sum(container.restart_count for container in (pod.status.container_statuses or [])),
                    "node": pod.spec.node_name,
                    "labels": pod.metadata.labels or {},
                    "annotations": pod.metadata.annotations or {},
                    "created_at": pod.metadata.creation_time.isoformat() if pod.metadata.creation_time else None,
                }
                for pod in response.items
            ]
        except ApiException as e:
            logger.error("Failed to list pods", namespace=namespace, error=str(e))
            raise KubernetesConnectionError(f"Failed to list pods: {e}")

    async def list_services(self, namespace: str) -> list[dict[str, Any]]:
        """List services in namespace."""
        self._ensure_connected()
        try:
            response = self._core_v1.list_namespaced_service(
                namespace=namespace,
                timeout_seconds=settings.kubernetes_timeout,
            )
            return [
                {
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "ports": [
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "protocol": port.protocol,
                        }
                        for port in (svc.spec.ports or [])
                    ],
                    "labels": svc.metadata.labels or {},
                    "annotations": svc.metadata.annotations or {},
                    "created_at": svc.metadata.creation_time.isoformat() if svc.metadata.creation_time else None,
                }
                for svc in response.items
            ]
        except ApiException as e:
            logger.error("Failed to list services", namespace=namespace, error=str(e))
            raise KubernetesConnectionError(f"Failed to list services: {e}")

    async def get_deployment(self, name: str, namespace: str) -> dict[str, Any] | None:
        """Get specific deployment."""
        self._ensure_connected()
        try:
            deploy = self._apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace,
                timeout_seconds=settings.kubernetes_timeout,
            )
            return {
                "name": deploy.metadata.name,
                "namespace": deploy.metadata.namespace,
                "replicas": deploy.spec.replicas,
                "available_replicas": deploy.status.available_replicas or 0,
                "ready_replicas": deploy.status.ready_replicas or 0,
                "updated_replicas": deploy.status.updated_replicas or 0,
                "labels": deploy.metadata.labels or {},
                "annotations": deploy.metadata.annotations or {},
                "created_at": deploy.metadata.creation_time.isoformat() if deploy.metadata.creation_time else None,
            }
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error("Failed to get deployment", name=name, namespace=namespace, error=str(e))
            raise KubernetesConnectionError(f"Failed to get deployment: {e}")

    async def get_pod(self, name: str, namespace: str) -> dict[str, Any] | None:
        """Get specific pod."""
        self._ensure_connected()
        try:
            pod = self._core_v1.read_namespaced_pod(
                name=name,
                namespace=namespace,
                timeout_seconds=settings.kubernetes_timeout,
            )
            return {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "ready": all(container.ready for container in (pod.status.container_statuses or [])),
                "restart_count": sum(container.restart_count for container in (pod.status.container_statuses or [])),
                "node": pod.spec.node_name,
                "labels": pod.metadata.labels or {},
                "annotations": pod.metadata.annotations or {},
                "created_at": pod.metadata.creation_time.isoformat() if pod.metadata.creation_time else None,
            }
        except ApiException as e:
            if e.status == 404:
                return None
            logger.error("Failed to get pod", name=name, namespace=namespace, error=str(e))
            raise KubernetesConnectionError(f"Failed to get pod: {e}")

    async def restart_deployment(self, name: str, namespace: str) -> bool:
        """Restart deployment via rollout restart."""
        self._ensure_connected()
        try:
            from kubernetes.client import V1RolloutConfig

            rollout_config = V1RolloutConfig()
            response = self._apps_v1.create_namespaced_deployment_rollout(
                name=name,
                namespace=namespace,
                body=rollout_config,
            )
            logger.info("Deployment restart initiated", name=name, namespace=namespace)
            return True
        except ApiException as e:
            logger.error("Failed to restart deployment", name=name, namespace=namespace, error=str(e))
            raise KubernetesConnectionError(f"Failed to restart deployment: {e}")

    async def scale_deployment(self, name: str, namespace: str, replicas: int) -> bool:
        """Scale deployment to specific replica count."""
        self._ensure_connected()
        try:
            from kubernetes.client import V1Scale

            scale = V1Scale(spec={"replicas": replicas})
            self._apps_v1.patch_namespaced_deployment_scale(
                name=name,
                namespace=namespace,
                body=scale,
            )
            logger.info("Deployment scaled", name=name, namespace=namespace, replicas=replicas)
            return True
        except ApiException as e:
            logger.error("Failed to scale deployment", name=name, namespace=namespace, error=str(e))
            raise KubernetesConnectionError(f"Failed to scale deployment: {e}")

    async def delete_pod(self, name: str, namespace: str) -> bool:
        """Delete a pod."""
        self._ensure_connected()
        try:
            self._core_v1.delete_namespaced_pod(
                name=name,
                namespace=namespace,
            )
            logger.info("Pod deleted", name=name, namespace=namespace)
            return True
        except ApiException as e:
            logger.error("Failed to delete pod", name=name, namespace=namespace, error=str(e))
            raise KubernetesConnectionError(f"Failed to delete pod: {e}")


class MockKubernetesClient(KubernetesClientInterface):
    """Mock Kubernetes client for testing and development."""

    def __init__(self):
        """Initialize mock client with sample data."""
        self._namespaces = [
            {"name": "default", "labels": {}, "status": "Active"},
            {"name": "staging", "labels": {"environment": "staging"}, "status": "Active"},
            {"name": "production", "labels": {"environment": "production"}, "status": "Active"},
        ]
        self._deployments = {
            "default": [
                {
                    "name": "demo-app",
                    "namespace": "default",
                    "replicas": 3,
                    "available_replicas": 3,
                    "ready_replicas": 3,
                    "updated_replicas": 3,
                    "labels": {"app": "demo"},
                    "annotations": {},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
            "staging": [
                {
                    "name": "api-service",
                    "namespace": "staging",
                    "replicas": 2,
                    "available_replicas": 2,
                    "ready_replicas": 2,
                    "updated_replicas": 2,
                    "labels": {"app": "api"},
                    "annotations": {},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
            "production": [
                {
                    "name": "payment-service",
                    "namespace": "production",
                    "replicas": 3,
                    "available_replicas": 2,
                    "ready_replicas": 2,
                    "updated_replicas": 3,
                    "labels": {"app": "payment"},
                    "annotations": {},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
        }
        self._pods = {
            "default": [
                {
                    "name": "demo-app-123",
                    "namespace": "default",
                    "phase": "Running",
                    "ready": True,
                    "restart_count": 0,
                    "node": "node-1",
                    "labels": {"app": "demo"},
                    "annotations": {},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
            "staging": [
                {
                    "name": "api-service-456",
                    "namespace": "staging",
                    "phase": "Running",
                    "ready": True,
                    "restart_count": 0,
                    "node": "node-2",
                    "labels": {"app": "api"},
                    "annotations": {},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ],
            "production": [
                {
                    "name": "payment-service-789",
                    "namespace": "production",
                    "phase": "Running",
                    "ready": True,
                    "restart_count": 8,
                    "node": "node-3",
                    "labels": {"app": "payment"},
                    "annotations": {},
                    "created_at": "2024-01-01T00:00:00Z",
                },
                {
                    "name": "payment-service-790",
                    "namespace": "production",
                    "phase": "CrashLoopBackOff",
                    "ready": False,
                    "restart_count": 15,
                    "node": "node-3",
                    "labels": {"app": "payment"},
                    "annotations": {},
                    "created_at": "2024-01-01T00:00:00Z",
                },
            ],
        }

    async def list_namespaces(self) -> list[dict[str, Any]]:
        """List all namespaces."""
        return self._namespaces

    async def list_deployments(self, namespace: str) -> list[dict[str, Any]]:
        """List deployments in namespace."""
        return self._deployments.get(namespace, [])

    async def list_pods(self, namespace: str) -> list[dict[str, Any]]:
        """List pods in namespace."""
        return self._pods.get(namespace, [])

    async def list_services(self, namespace: str) -> list[dict[str, Any]]:
        """List services in namespace."""
        return []

    async def get_deployment(self, name: str, namespace: str) -> dict[str, Any] | None:
        """Get specific deployment."""
        deployments = self._deployments.get(namespace, [])
        for deploy in deployments:
            if deploy["name"] == name:
                return deploy
        return None

    async def get_pod(self, name: str, namespace: str) -> dict[str, Any] | None:
        """Get specific pod."""
        pods = self._pods.get(namespace, [])
        for pod in pods:
            if pod["name"] == name:
                return pod
        return None

    async def restart_deployment(self, name: str, namespace: str) -> bool:
        """Restart deployment via rollout restart."""
        logger.info("Mock: Deployment restart initiated", name=name, namespace=namespace)
        return True

    async def scale_deployment(self, name: str, namespace: str, replicas: int) -> bool:
        """Scale deployment to specific replica count."""
        logger.info("Mock: Deployment scaled", name=name, namespace=namespace, replicas=replicas)
        deployments = self._deployments.get(namespace, [])
        for deploy in deployments:
            if deploy["name"] == name:
                deploy["replicas"] = replicas
                deploy["available_replicas"] = replicas
                deploy["ready_replicas"] = replicas
        return True

    async def delete_pod(self, name: str, namespace: str) -> bool:
        """Delete a pod."""
        logger.info("Mock: Pod deleted", name=name, namespace=namespace)
        pods = self._pods.get(namespace, [])
        self._pods[namespace] = [pod for pod in pods if pod["name"] != name]
        return True


def get_kubernetes_client(use_mock: bool = False) -> KubernetesClientInterface:
    """Get Kubernetes client instance."""
    if use_mock or settings.is_development:
        logger.info("Using mock Kubernetes client")
        return MockKubernetesClient()
    return KubernetesClient()
