"""Alert domain model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums.incident_severity import IncidentSeverity


class Alert(BaseModel):
    """Represents an alert."""

    id: str | None = None
    workload: str
    namespace: str
    severity: IncidentSeverity
    title: str
    message: str
    metric_name: str
    threshold: float
    current_value: float
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    is_resolved: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
