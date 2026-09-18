"""SQLAlchemy database models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.domain.enums.health_status import HealthStatus
from app.domain.enums.incident_severity import IncidentSeverity
from app.domain.enums.incident_status import IncidentStatus
from app.domain.enums.incident_type import IncidentType
from app.domain.enums.remediation_action import RemediationAction
from app.domain.enums.remediation_status import RemediationStatus


class WorkloadModel(Base):
    """Workload database model."""

    __tablename__ = "workloads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    desired_replicas: Mapped[int] = mapped_column(Integer, nullable=False)
    available_replicas: Mapped[int] = mapped_column(Integer, nullable=False)
    health: Mapped[str] = mapped_column(String(20), nullable=False, default=HealthStatus.UNKNOWN.value)
    restart_count: Mapped[int] = mapped_column(Integer, default=0)
    cpu_usage_percent: Mapped[float] = mapped_column(Float, default=0.0)
    memory_usage_percent: Mapped[float] = mapped_column(Float, default=0.0)
    error_rate: Mapped[float] = mapped_column(Float, default=0.0)
    response_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    labels: Mapped[dict] = mapped_column(JSONB, default={})
    annotations: Mapped[dict] = mapped_column(JSONB, default={})
    metadata: Mapped[dict] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    incidents = relationship("IncidentModel", back_populates="workload_rel", cascade="all, delete-orphan")
    alerts = relationship("AlertModel", back_populates="workload_rel", cascade="all, delete-orphan")
    remediation_actions = relationship("RemediationActionModel", back_populates="workload_rel", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_workload_namespace_name", "namespace", "name"),
    )


class IncidentModel(Base):
    """Incident database model."""

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workload: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=IncidentStatus.OPEN.value, index=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default={})
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign key to workload
    workload_id: Mapped[str] = mapped_column(String(36), ForeignKey("workloads.id"), nullable=True)

    # Relationships
    workload_rel = relationship("WorkloadModel", back_populates="incidents")
    remediation_actions = relationship("RemediationActionModel", back_populates="incident_rel", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_incident_status_severity", "status", "severity"),
        Index("idx_incident_workload_namespace", "workload", "namespace"),
    )


class AlertModel(Base):
    """Alert database model."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workload: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default={})

    # Foreign key to workload
    workload_id: Mapped[str] = mapped_column(String(36), ForeignKey("workloads.id"), nullable=True)

    # Relationships
    workload_rel = relationship("WorkloadModel", back_populates="alerts")

    __table_args__ = (
        Index("idx_alert_resolved_severity", "is_resolved", "severity"),
    )


class RemediationActionModel(Base):
    """Remediation action database model."""

    __tablename__ = "remediation_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=True, index=True)
    workload: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=RemediationStatus.PENDING.value, index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    initiated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata: Mapped[dict] = mapped_column(JSONB, default={})

    # Foreign key to workload
    workload_id: Mapped[str] = mapped_column(String(36), ForeignKey("workloads.id"), nullable=True)

    # Relationships
    workload_rel = relationship("WorkloadModel", back_populates="remediation_actions")
    incident_rel = relationship("IncidentModel", back_populates="remediation_actions")

    __table_args__ = (
        Index("idx_remediation_status_workload", "status", "workload"),
    )


class HealthCheckModel(Base):
    """Health check database model."""

    __tablename__ = "health_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workload: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default={})

    __table_args__ = (
        Index("idx_health_check_workload_time", "workload", "checked_at"),
    )


class AuditEventModel(Base):
    """Audit event database model."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=True)
    workload: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    namespace: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, default={})
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_audit_event_type_time", "event_type", "timestamp"),
    )
