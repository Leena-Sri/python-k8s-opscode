"""Unit tests for monitoring service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.monitoring_service import MonitoringService
from app.domain.models.workload import Workload
from app.domain.models.incident import Incident
from app.domain.enums.health_status import HealthStatus
from app.domain.enums.incident_type import IncidentType
from app.domain.enums.incident_severity import IncidentSeverity


class TestMonitoringService:
    """Test cases for MonitoringService."""

    @pytest.fixture
    def workload_service(self):
        """Create a mock workload service."""
        return Mock()

    @pytest.fixture
    def cache(self):
        """Create a mock cache."""
        return Mock()

    @pytest.fixture
    def monitoring_service(self, workload_service, cache):
        """Create a monitoring service instance."""
        service = MonitoringService(workload_service, cache)
        service.set_incident_service(Mock())
        return service

    @pytest.mark.asyncio
    async def test_start_stop(self, monitoring_service):
        """Test starting and stopping monitoring service."""
        await monitoring_service.start()
        assert monitoring_service._running is True

        await monitoring_service.stop()
        assert monitoring_service._running is False

    @pytest.mark.asyncio
    async def test_evaluate_workload_health_healthy(self, monitoring_service):
        """Test health evaluation for healthy workload."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=3,
            health=HealthStatus.HEALTHY,
            restart_count=0,
        )

        result = await monitoring_service._evaluate_workload_health(workload)

        assert result["healthy"] is True
        assert result["workload"] == "test-service"
        assert len(result["checks"]) > 0

    @pytest.mark.asyncio
    async def test_evaluate_workload_health_degraded(self, monitoring_service):
        """Test health evaluation for degraded workload."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=2,
            health=HealthStatus.DEGRADED,
            restart_count=3,
        )

        result = await monitoring_service._evaluate_workload_health(workload)

        assert result["healthy"] is False
        assert result["workload"] == "test-service"

    @pytest.mark.asyncio
    async def test_evaluate_workload_health_unhealthy(self, monitoring_service):
        """Test health evaluation for unhealthy workload."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=3,
            health=HealthStatus.UNHEALTHY,
            restart_count=10,
        )

        result = await monitoring_service._evaluate_workload_health(workload)

        assert result["healthy"] is False
        assert result["workload"] == "test-service"

    @pytest.mark.asyncio
    async def test_detect_incidents_crash_loop(self, monitoring_service):
        """Test incident detection for crash loop."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=3,
            health=HealthStatus.UNHEALTHY,
            restart_count=10,
        )

        with patch('app.services.monitoring_service.settings') as mock_settings:
            mock_settings.restart_threshold = 5
            incidents = await monitoring_service._detect_incidents(workload)

            assert len(incidents) > 0
            assert any(inc.type == IncidentType.POD_CRASH_LOOP for inc in incidents)

    @pytest.mark.asyncio
    async def test_detect_incidents_replica_shortage(self, monitoring_service):
        """Test incident detection for replica shortage."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=1,
            health=HealthStatus.DEGRADED,
            restart_count=0,
        )

        with patch('app.services.monitoring_service.settings') as mock_settings:
            mock_settings.replica_shortage_threshold = 1
            incidents = await monitoring_service._detect_incidents(workload)

            assert len(incidents) > 0
            assert any(inc.type == IncidentType.REPLICA_SHORTAGE for inc in incidents)

    @pytest.mark.asyncio
    async def test_detect_incidents_high_cpu(self, monitoring_service):
        """Test incident detection for high CPU."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=3,
            health=HealthStatus.HEALTHY,
            restart_count=0,
            cpu_usage_percent=90.0,
        )

        with patch('app.services.monitoring_service.settings') as mock_settings:
            mock_settings.cpu_threshold_percent = 80.0
            incidents = await monitoring_service._detect_incidents(workload)

            assert len(incidents) > 0
            assert any(inc.type == IncidentType.HIGH_CPU for inc in incidents)

    @pytest.mark.asyncio
    async def test_detect_incidents_no_issues(self, monitoring_service):
        """Test incident detection when no issues exist."""
        workload = Workload(
            name="test-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            available_replicas=3,
            health=HealthStatus.HEALTHY,
            restart_count=0,
            cpu_usage_percent=45.0,
            memory_usage_percent=50.0,
        )

        with patch('app.services.monitoring_service.settings') as mock_settings:
            mock_settings.restart_threshold = 5
            mock_settings.cpu_threshold_percent = 80.0
            mock_settings.memory_threshold_percent = 85.0
            incidents = await monitoring_service._detect_incidents(workload)

            assert len(incidents) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
