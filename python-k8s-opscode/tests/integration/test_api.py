"""Integration tests for FastAPI endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock, patch

from app.main import create_app


@pytest.fixture
def app():
    """Create FastAPI application instance."""
    return create_app()


@pytest.fixture
async def client(app):
    """Create async HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Test cases for health endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = await client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

    @pytest.mark.asyncio
    async def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_liveness_check(self, client):
        """Test liveness check endpoint."""
        response = await client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestWorkloadEndpoints:
    """Test cases for workload endpoints."""

    @pytest.mark.asyncio
    async def test_list_workloads(self, client):
        """Test listing workloads endpoint."""
        with patch('app.api.routes.workloads.get_workload_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.get_workloads = AsyncMock(return_value=[])

            response = await client.get("/api/v1/workloads")
            assert response.status_code == 200
            data = response.json()
            assert "workloads" in data

    @pytest.mark.asyncio
    async def test_list_workloads_with_namespace_filter(self, client):
        """Test listing workloads with namespace filter."""
        with patch('app.api.routes.workloads.get_workload_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.get_workloads = AsyncMock(return_value=[])

            response = await client.get("/api/v1/workloads?namespace=default")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_workload(self, client):
        """Test getting specific workload endpoint."""
        with patch('app.api.routes.workloads.get_workload_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.get_workload = AsyncMock(return_value=Mock(
                name="test-service",
                namespace="default",
                health="HEALTHY"
            ))

            response = await client.get("/api/v1/workloads/test-service?namespace=default")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_namespaces(self, client):
        """Test listing namespaces endpoint."""
        with patch('app.api.routes.workloads.get_workload_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.get_workloads = AsyncMock(return_value=[])

            response = await client.get("/api/v1/namespaces")
            assert response.status_code == 200
            data = response.json()
            assert "namespaces" in data


class TestIncidentEndpoints:
    """Test cases for incident endpoints."""

    @pytest.mark.asyncio
    async def test_list_incidents(self, client):
        """Test listing incidents endpoint."""
        with patch('app.api.routes.incidents.get_incident_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.list_incidents = AsyncMock(return_value=[])

            response = await client.get("/api/v1/incidents")
            assert response.status_code == 200
            data = response.json()
            assert "incidents" in data

    @pytest.mark.asyncio
    async def test_list_incidents_with_filters(self, client):
        """Test listing incidents with filters."""
        with patch('app.api.routes.incidents.get_incident_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.list_incidents = AsyncMock(return_value=[])

            response = await client.get("/api/v1/incidents?status=OPEN&severity=CRITICAL")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_acknowledge_incident(self, client):
        """Test acknowledging incident endpoint."""
        with patch('app.api.routes.incidents.get_incident_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.acknowledge_incident = AsyncMock(return_value=Mock(
                id="incident-123",
                status="ACKNOWLEDGED"
            ))

            response = await client.post("/api/v1/incidents/incident-123/acknowledge")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resolve_incident(self, client):
        """Test resolving incident endpoint."""
        with patch('app.api.routes.incidents.get_incident_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.resolve_incident = AsyncMock(return_value=Mock(
                id="incident-123",
                status="RESOLVED"
            ))

            response = await client.post("/api/v1/incidents/incident-123/resolve", json={
                "resolution_notes": "Issue resolved"
            })
            assert response.status_code == 200


class TestRemediationEndpoints:
    """Test cases for remediation endpoints."""

    @pytest.mark.asyncio
    async def test_list_remediation_actions(self, client):
        """Test listing remediation actions endpoint."""
        with patch('app.api.routes.remediation.get_remediation_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.list_remediation_actions = AsyncMock(return_value=[])

            response = await client.get("/api/v1/remediation/actions")
            assert response.status_code == 200
            data = response.json()
            assert "actions" in data

    @pytest.mark.asyncio
    async def test_restart_workload(self, client):
        """Test restarting workload endpoint."""
        with patch('app.api.routes.remediation.get_remediation_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.execute_remediation = AsyncMock(return_value=Mock(
                workload="test-service",
                action="RESTART",
                status="SUCCESS"
            ))

            response = await client.post("/api/v1/remediation/test-service/restart?namespace=default")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_scale_workload(self, client):
        """Test scaling workload endpoint."""
        with patch('app.api.routes.remediation.get_remediation_service') as mock_service:
            mock_service.return_value = Mock()
            mock_service.return_value.execute_remediation = AsyncMock(return_value=Mock(
                workload="test-service",
                action="SCALE",
                status="SUCCESS"
            ))

            response = await client.post("/api/v1/remediation/test-service/scale?namespace=default&replicas=5")
            assert response.status_code == 200


class TestMetricsEndpoints:
    """Test cases for metrics endpoints."""

    @pytest.mark.asyncio
    async def test_metrics_summary(self, client):
        """Test metrics summary endpoint."""
        with patch('app.api.routes.metrics.get_db_session') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=Mock())
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

            response = await client.get("/api/v1/metrics/summary")
            assert response.status_code == 200
            data = response.json()
            assert "workloads" in data
            assert "incidents" in data
            assert "remediations" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
