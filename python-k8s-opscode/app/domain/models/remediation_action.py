"""Remediation action domain model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums.remediation_action import RemediationAction
from app.domain.enums.remediation_status import RemediationStatus


class RemediationAction(BaseModel):
    """Represents a remediation action."""

    id: str | None = None
    incident_id: str | None = None
    workload: str
    namespace: str
    action: RemediationAction
    status: RemediationStatus = Field(default=RemediationStatus.PENDING)
    dry_run: bool = Field(default=True)
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = Field(default=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True

    @property
    def is_successful(self) -> bool:
        """Check if remediation was successful."""
        return self.status == RemediationStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """Check if remediation failed."""
        return self.status == RemediationStatus.FAILED

    @property
    def duration_seconds(self) -> float | None:
        """Calculate remediation duration in seconds."""
        if self.completed_at:
            delta = self.completed_at - self.initiated_at
            return delta.total_seconds()
        return None
