"""Unit tests for remediation service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.remediation_service import RemediationService
from app.domain.models.remediation_action import RemediationAction
from app.domain.models.incident import Incident
from app.domain.enums.remediation_action import RemediationAction as RemediationActionEnum
from app.domain.enums.remediation_status import RemediationStatus
from app.domain.enums.incident_type import IncidentType
from app.domain.enums.incident_severity import IncidentSeverity


class TestRemediationService:
    """Test cases for RemediationService."""

    @pytest.fixture
    def workload_manager(self):
        """Create a mock workload manager."""
        return Mock()

    @pytest.fixture
    def cache(self):
        """Create a mock cache."""
        mock_cache = Mock()
        mock_cache._client = Mock()
        return mock_cache

    @pytest.fixture
    def remediation_service(self, workload_manager, cache):
        """Create a remediation service instance."""
        return RemediationService(workload_manager, cache)

    @pytest.mark.asyncio
    async def test_evaluate_remediation_pod_crash_loop(self, remediation_service):
        """Test remediation evaluation for pod crash loop."""
        incident = Incident(
            workload="test-service",
            namespace="default",
            severity=IncidentSeverity.CRITICAL,
            type=IncidentType.POD_CRASH_LOOP,
            description="Pods in CrashLoopBackOff",
        )

        with patch('app.services.remediation_service.settings') as mock_settings:
            mock_settings.remediation_enabled = True
            mock_settings.remediation_allowed_namespaces = ["default", "staging"]
            mock_settings.remediation_allowed_workloads = []
            mock_settings.remediation_dry_run = True

            result = await remediation_service.evaluate_remediation(incident)

            assert result is not None
            assert result.action == RemediationActionEnum.RESTART
            assert result.dry_run is True

    @pytest.mark.asyncio
    async def test_evaluate_remediation_disabled(self, remediation_service):
        """Test remediation evaluation when disabled."""
        incident = Incident(
            workload="test-service",
            namespace="default",
            severity=IncidentSeverity.CRITICAL,
            type=IncidentType.POD_CRASH_LOOP,
            description="Pods in CrashLoopBackOff",
        )

        with patch('app.services.remediation_service.settings') as mock_settings:
            mock_settings.remediation_enabled = False

            result = await remediation_service.evaluate_remediation(incident)

            assert result is None

    @pytest.mark.asyncio
    async def test_evaluate_remediation_namespace_not_allowed(self, remediation_service):
        """Test remediation evaluation for disallowed namespace."""
        incident = Incident(
            workload="test-service",
            namespace="production",
            severity=IncidentSeverity.CRITICAL,
            type=IncidentType.POD_CRASH_LOOP,
            description="Pods in CrashLoopBackOff",
        )

        with patch('app.services.remediation_service.settings') as mock_settings:
            mock_settings.remediation_enabled = True
            mock_settings.remediation_allowed_namespaces = ["default", "staging"]

            result = await remediation_service.evaluate_remediation(incident)

            assert result is None

    @pytest.mark.asyncio
    async def test_execute_remediation_dry_run(self, remediation_service, cache):
        """Test executing remediation in dry run mode."""
        remediation = RemediationAction(
            workload="test-service",
            namespace="default",
            action=RemediationActionEnum.RESTART,
            dry_run=True,
        )

        cache._client.set = AsyncMock(return_value=True)
        cache._client.exists = AsyncMock(return_value=False)
        cache._client.delete = AsyncMock(return_value=True)

        result = await remediation_service.execute_remediation(remediation)

        assert result.status == RemediationStatus.SUCCESS
        assert result.dry_run is True
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_remediation_actual(self, remediation_service, workload_manager, cache):
        """Test executing actual remediation."""
        remediation = RemediationAction(
            workload="test-service",
            namespace="default",
            action=RemediationActionEnum.RESTART,
            dry_run=False,
        )

        workload_manager.restart_workload = AsyncMock(return_value=True)
        cache._client.set = AsyncMock(return_value=True)
        cache._client.exists = AsyncMock(return_value=False)
        cache._client.delete = AsyncMock(return_value=True)

        result = await remediation_service.execute_remediation(remediation)

        assert result.status == RemediationStatus.SUCCESS
        assert result.dry_run is False
        workload_manager.restart_workload.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_remediation_failure(self, remediation_service, workload_manager, cache):
        """Test remediation execution failure."""
        remediation = RemediationAction(
            workload="test-service",
            namespace="default",
            action=RemediationActionEnum.RESTART,
            dry_run=False,
        )

        workload_manager.restart_workload = AsyncMock(side_effect=Exception("Failed to restart"))
        cache._client.set = AsyncMock(return_value=True)
        cache._client.exists = AsyncMock(return_value=False)
        cache._client.delete = AsyncMock(return_value=True)

        with pytest.raises(Exception):
            await remediation_service.execute_remediation(remediation)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
