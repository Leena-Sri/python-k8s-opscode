"""Incident domain model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums.incident_severity import IncidentSeverity
from app.domain.enums.incident_status import IncidentStatus
from app.domain.enums.incident_type import IncidentType


class Incident(BaseModel):
    """Represents an operational incident."""

    id: str | None = None
    workload: str
    namespace: str
    severity: IncidentSeverity
    type: IncidentType
    description: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    status: IncidentStatus = Field(default=IncidentStatus.OPEN)
    metadata: dict[str, Any] = Field(default_factory=dict)
    resolution_notes: str | None = None

    class Config:
        """Pydantic configuration."""

        use_enum_values = True

    @property
    def is_open(self) -> bool:
        """Check if incident is open."""
        return self.status == IncidentStatus.OPEN

    @property
    def is_resolved(self) -> bool:
        """Check if incident is resolved."""
        return self.status == IncidentStatus.RESOLVED

    @property
    def duration_minutes(self) -> float | None:
        """Calculate incident duration in minutes."""
        if self.resolved_at:
            delta = self.resolved_at - self.detected_at
            return delta.total_seconds() / 60
        return None
