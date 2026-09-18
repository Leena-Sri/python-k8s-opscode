"""Unit tests for Kubernetes client."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.kubernetes.client import MockKubernetesClient, KubernetesClientInterface


class TestMockKubernetesClient:
    """Test cases for MockKubernetesClient."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Kubernetes client."""
        return MockKubernetesClient()

    @pytest.mark.asyncio
    async def test_list_namespaces(self, mock_client):
        """Test listing namespaces."""
        namespaces = await mock_client.list_namespaces()
        assert len(namespaces) == 3
        assert any(ns["name"] == "default" for ns in namespaces)
        assert any(ns["name"] == "staging" for ns in namespaces)
        assert any(ns["name"] == "production" for ns in namespaces)

    @pytest.mark.asyncio
    async def test_list_deployments(self, mock_client):
        """Test listing deployments."""
        deployments = await mock_client.list_deployments("default")
        assert len(deployments) == 1
        assert deployments[0]["name"] == "demo-app"
        assert deployments[0]["namespace"] == "default"

    @pytest.mark.asyncio
    async def test_list_pods(self, mock_client):
        """Test listing pods."""
        pods = await mock_client.list_pods("production")
        assert len(pods) == 2
        assert any(pod["phase"] == "CrashLoopBackOff" for pod in pods)

    @pytest.mark.asyncio
    async def test_get_deployment(self, mock_client):
        """Test getting a specific deployment."""
        deployment = await mock_client.get_deployment("demo-app", "default")
        assert deployment is not None
        assert deployment["name"] == "demo-app"
        assert deployment["namespace"] == "default"

    @pytest.mark.asyncio
    async def test_get_deployment_not_found(self, mock_client):
        """Test getting a non-existent deployment."""
        deployment = await mock_client.get_deployment("nonexistent", "default")
        assert deployment is None

    @pytest.mark.asyncio
    async def test_restart_deployment(self, mock_client):
        """Test restarting a deployment."""
        result = await mock_client.restart_deployment("demo-app", "default")
        assert result is True

    @pytest.mark.asyncio
    async def test_scale_deployment(self, mock_client):
        """Test scaling a deployment."""
        result = await mock_client.scale_deployment("demo-app", "default", 5)
        assert result is True

        # Verify the deployment was scaled
        deployment = await mock_client.get_deployment("demo-app", "default")
        assert deployment["replicas"] == 5

    @pytest.mark.asyncio
    async def test_delete_pod(self, mock_client):
        """Test deleting a pod."""
        initial_pods = await mock_client.list_pods("production")
        initial_count = len(initial_pods)

        result = await mock_client.delete_pod("payment-service-790", "production")
        assert result is True

        final_pods = await mock_client.list_pods("production")
        assert len(final_pods) == initial_count - 1


class TestKubernetesClientInterface:
    """Test cases for Kubernetes client interface."""

    def test_interface_methods(self):
        """Test that interface has required methods."""
        required_methods = [
            'list_namespaces',
            'list_deployments',
            'list_pods',
            'list_services',
            'get_deployment',
            'get_pod',
            'restart_deployment',
            'scale_deployment',
            'delete_pod',
        ]

        for method in required_methods:
            assert hasattr(KubernetesClientInterface, method)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
