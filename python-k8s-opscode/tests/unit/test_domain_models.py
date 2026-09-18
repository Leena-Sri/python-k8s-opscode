"""Unit tests for domain models."""

from datetime import datetime
import pytest

from app.domain.models.workload import Workload
from app.domain.models.incident import Incident
from app.domain.models.alert import Alert
from app.domain.models.remediation_action import RemediationAction
from app.domain.enums.health_status import HealthStatus
from app.domain.enums.incident_severity import IncidentSeverity
from app.domain.enums.incident_status import IncidentStatus
from app.domain.enums.incident_type import IncidentType
from app.domain.enums.remediation_action import RemediationAction as RemediationActionEnum
from app.domain.enums.remediation_status import RemediationStatus


class TestWorkload:
    """Test cases for Workload model."""

    def test_workload_creation(self):
        """Test creating a workload."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=3,
        )
        assert workload.name == "test-service"
        assert workload.namespace == "default"
        assert workload.health == HealthStatus.UNKNOWN

    def test_workload_is_healthy(self):
        """Test workload health check."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=3,
            health=HealthStatus.HEALTHY,
            restart_count=0,
        )
        assert workload.is_healthy is True
        assert workload.is_degraded is False

    def test_workload_is_degraded(self):
        """Test degraded workload detection."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=2,
            health=HealthStatus.DEGRADED,
            restart_count=3,
        )
        assert workload.is_healthy is False
        assert workload.is_degraded is True

    def test_workload_unhealthy_due_to_restarts(self):
        """Test unhealthy workload due to high restart count."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=3,
            health=HealthStatus.HEALTHY,
            restart_count=10,
        )
        assert workload.is_healthy is False
        assert workload.is_degraded is True


class TestIncident:
    """Test cases for Incident model."""

    def test_incident_creation(self):
        """Test creating an incident."""
        incident = Incident(
            workload="test-service",
            namespace="default",
            severity=IncidentSeverity.CRITICAL,
            type=IncidentType.POD_CRASH_LOOP,
            description="Pods in CrashLoopBackOff",
        )
        assert incident.workload == "test-service"
        assert incident.severity == IncidentSeverity.CRITICAL
        assert incident.status == IncidentStatus.OPEN

    def test_incident_is_open(self):
        """Test incident open status."""
        incident = Incident(
            workload="test-service",
            namespace="default",
            severity=IncidentSeverity.CRITICAL,
            type=IncidentType.POD_CRASH_LOOP,
            description="Pods in CrashLoopBackOff",
            status=IncidentStatus.OPEN,
        )
        assert incident.is_open is True
        assert incident.is_resolved is False

    def test_incident_is_resolved(self):
        """Test incident resolved status."""
        incident = Incident(
            workload="test-service",
            namespace="default",
            severity=IncidentSeverity.CRITICAL,
            type=IncidentType.POD_CRASH_LOOP,
            description="Pods in CrashLoopBackOff",
            status=IncidentStatus.RESOLVED,
            resolved_at=datetime.utcnow(),
        )
        assert incident.is_open is False
        assert incident.is_resolved is True

    def test_incident_duration(self):
        """Test incident duration calculation."""
        detected_at = datetime.utcnow()
        resolved_at = datetime.utcnow()
        incident = Incident(
            workload="test-service",
            namespace="default",
            severity=IncidentSeverity.CRITICAL,
            type=IncidentType.POD_CRASH_LOOP,
            description="Pods in CrashLoopBackOff",
            detected_at=detected_at,
            resolved_at=resolved_at,
            status=IncidentStatus.RESOLVED,
        )
        duration = incident.duration_minutes
        assert duration is not None
        assert duration >= 0


class TestRemediationAction:
    """Test cases for RemediationAction model."""

    def test_remediation_creation(self):
        """Test creating a remediation action."""
        remediation = RemediationAction(
            workload="test-service",
            namespace="default",
            action=RemediationActionEnum.RESTART,
            dry_run=True,
        )
        assert remediation.workload == "test-service"
        assert remediation.action == RemediationActionEnum.RESTART
        assert remediation.status == RemediationStatus.PENDING
        assert remediation.dry_run is True

    def test_remediation_is_successful(self):
        """Test successful remediation."""
        remediation = RemediationAction(
            workload="test-service",
            namespace="default",
            action=RemediationActionEnum.RESTART,
            status=RemediationStatus.SUCCESS,
            completed_at=datetime.utcnow(),
        )
        assert remediation.is_successful is True
        assert remediation.is_failed is False

    def test_remediation_is_failed(self):
        """Test failed remediation."""
        remediation = RemediationAction(
            workload="test-service",
            namespace="default",
            action=RemediationActionEnum.RESTART,
            status=RemediationStatus.FAILED,
            error_message="Failed to restart",
            completed_at=datetime.utcnow(),
        )
        assert remediation.is_successful is False
        assert remediation.is_failed is True

    def test_remediation_duration(self):
        """Test remediation duration calculation."""
        initiated_at = datetime.utcnow()
        completed_at = datetime.utcnow()
        remediation = RemediationAction(
            workload="test-service",
            namespace="default",
            action=RemediationActionEnum.RESTART,
            initiated_at=initiated_at,
            completed_at=completed_at,
            status=RemediationStatus.SUCCESS,
        )
        duration = remediation.duration_seconds
        assert duration is not None
        assert duration >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
