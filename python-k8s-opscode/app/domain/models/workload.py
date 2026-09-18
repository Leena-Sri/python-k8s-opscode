"""Workload domain model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums.health_status import HealthStatus


class Workload(BaseModel):
    """Represents a Kubernetes workload."""

    name: str
    namespace: str
    kind: str  # Deployment, StatefulSet, DaemonSet, etc.
    desired_replicas: int
    available_replicas: int
    health: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    restart_count: int = Field(default=0)
    cpu_usage_percent: float = Field(default=0.0)
    memory_usage_percent: float = Field(default=0.0)
    error_rate: float = Field(default=0.0)
    response_latency_ms: float = Field(default=0.0)
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True

    @property
    def is_healthy(self) -> bool:
        """Check if workload is healthy."""
        return (
            self.health == HealthStatus.HEALTHY
            and self.available_replicas >= self.desired_replicas
            and self.restart_count < 5
        )

    @property
    def is_degraded(self) -> bool:
        """Check if workload is degraded."""
        return (
            self.health == HealthStatus.DEGRADED
            or self.available_replicas < self.desired_replicas
            or self.restart_count >= 5
        )
