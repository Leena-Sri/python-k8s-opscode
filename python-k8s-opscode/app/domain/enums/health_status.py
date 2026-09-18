"""Health status enumeration for workloads."""

from enum import Enum


class HealthStatus(str, Enum):
    """Health status of a workload."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"
