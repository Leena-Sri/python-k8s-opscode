"""Base cloud provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class CloudProvider(ABC):
    """Abstract base class for cloud providers."""

    @abstractmethod
    async def get_cluster_info(self) -> dict[str, Any]:
        """Get information about the Kubernetes cluster."""
        pass

    @abstractmethod
    async def get_node_info(self) -> list[dict[str, Any]]:
        """Get information about cluster nodes."""
        pass

    @abstractmethod
    async def get_workload_metrics(self, workload_name: str, namespace: str) -> dict[str, Any]:
        """Get detailed metrics for a specific workload."""
        pass

    @abstractmethod
    async def scale_cluster(self, node_count: int) -> bool:
        """Scale the cluster to the specified number of nodes."""
        pass

    @abstractmethod
    async def get_cost_data(self, time_range: str) -> dict[str, Any]:
        """Get cost data for the specified time range."""
        pass

    @abstractmethod
    async def get_logs(self, workload_name: str, namespace: str, lines: int = 100) -> list[str]:
        """Get logs for a specific workload."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the cloud provider is available."""
        pass
