"""Unit tests for Redis cache layer."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

from app.cache.redis import RedisCache, DistributedLock, workload_key, incident_key, remediation_lock_key


class TestRedisCache:
    """Test cases for RedisCache."""

    @pytest.fixture
    def redis_client(self):
        """Create a mock Redis client."""
        return Mock()

    @pytest.fixture
    def cache(self, redis_client):
        """Create a Redis cache instance."""
        return RedisCache(redis_client)

    @pytest.mark.asyncio
    async def test_get_string(self, cache, redis_client):
        """Test getting a string value."""
        redis_client.get = AsyncMock(return_value="test_value")
        result = await cache.get("test_key")
        assert result == "test_value"
        redis_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_json(self, cache, redis_client):
        """Test getting a JSON value."""
        json_data = {"key": "value"}
        redis_client.get = AsyncMock(return_value=json.dumps(json_data))
        result = await cache.get("test_key")
        assert result == json_data

    @pytest.mark.asyncio
    async def test_get_not_found(self, cache, redis_client):
        """Test getting a non-existent key."""
        redis_client.get = AsyncMock(return_value=None)
        result = await cache.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_string(self, cache, redis_client):
        """Test setting a string value."""
        redis_client.set = AsyncMock(return_value=True)
        result = await cache.set("test_key", "test_value")
        assert result is True
        redis_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_json(self, cache, redis_client):
        """Test setting a JSON value."""
        json_data = {"key": "value"}
        redis_client.set = AsyncMock(return_value=True)
        result = await cache.set("test_key", json_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache, redis_client):
        """Test setting a value with TTL."""
        redis_client.setex = AsyncMock(return_value=True)
        result = await cache.set("test_key", "test_value", ttl=60)
        assert result is True
        redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self, cache, redis_client):
        """Test deleting a key."""
        redis_client.delete = AsyncMock(return_value=True)
        result = await cache.delete("test_key")
        assert result is True
        redis_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists(self, cache, redis_client):
        """Test checking if a key exists."""
        redis_client.exists = AsyncMock(return_value=1)
        result = await cache.exists("test_key")
        assert result is True
        redis_client.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_not_found(self, cache, redis_client):
        """Test checking if a non-existent key exists."""
        redis_client.exists = AsyncMock(return_value=0)
        result = await cache.exists("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_expire(self, cache, redis_client):
        """Test setting TTL for existing key."""
        redis_client.expire = AsyncMock(return_value=True)
        result = await cache.expire("test_key", 60)
        assert result is True
        redis_client.expire.assert_called_once_with("test_key", 60)

    @pytest.mark.asyncio
    async def test_ttl(self, cache, redis_client):
        """Test getting TTL for a key."""
        redis_client.ttl = AsyncMock(return_value=60)
        result = await cache.ttl("test_key")
        assert result == 60
        redis_client.ttl.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_keys(self, cache, redis_client):
        """Test getting keys matching pattern."""
        redis_client.keys = AsyncMock(return_value=["key1", "key2"])
        result = await cache.keys("test:*")
        assert result == ["key1", "key2"]
        redis_client.keys.assert_called_once_with("test:*")

    @pytest.mark.asyncio
    async def test_increment(self, cache, redis_client):
        """Test incrementing a counter."""
        redis_client.incrby = AsyncMock(return_value=1)
        result = await cache.increment("test_key")
        assert result == 1
        redis_client.incrby.assert_called_once_with("test_key", 1)

    @pytest.mark.asyncio
    async def test_decrement(self, cache, redis_client):
        """Test decrementing a counter."""
        redis_client.decrby = AsyncMock(return_value=0)
        result = await cache.decrement("test_key")
        assert result == 0
        redis_client.decrby.assert_called_once_with("test_key", 1)


class TestDistributedLock:
    """Test cases for DistributedLock."""

    @pytest.fixture
    def redis_client(self):
        """Create a mock Redis client."""
        return Mock()

    @pytest.fixture
    def lock(self, redis_client):
        """Create a distributed lock instance."""
        return DistributedLock(redis_client)

    @pytest.mark.asyncio
    async def test_acquire_lock(self, lock, redis_client):
        """Test acquiring a lock."""
        redis_client.set = AsyncMock(return_value=True)
        result = await lock.acquire("test_lock", ttl=30)
        assert result is True
        redis_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_lock_timeout(self, lock, redis_client):
        """Test lock acquisition timeout."""
        redis_client.set = AsyncMock(return_value=False)
        result = await lock.acquire("test_lock", ttl=30, wait_timeout=1)
        assert result is False

    @pytest.mark.asyncio
    async def test_release_lock(self, lock, redis_client):
        """Test releasing a lock."""
        redis_client.delete = AsyncMock(return_value=True)
        result = await lock.release("test_lock")
        assert result is True
        redis_client.delete.assert_called_once_with("test_lock")

    @pytest.mark.asyncio
    async def test_is_locked(self, lock, redis_client):
        """Test checking if lock is held."""
        redis_client.exists = AsyncMock(return_value=1)
        result = await lock.is_locked("test_lock")
        assert result is True
        redis_client.exists.assert_called_once_with("test_lock")


class TestCacheKeyGenerators:
    """Test cases for cache key generators."""

    def test_workload_key(self):
        """Test workload key generation."""
        key = workload_key("default", "test-service")
        assert key == "workload:default:test-service"

    def test_incident_key(self):
        """Test incident key generation."""
        key = incident_key("incident-123")
        assert key == "incident:incident-123"

    def test_remediation_lock_key(self):
        """Test remediation lock key generation."""
        key = remediation_lock_key("test-service", "default")
        assert key == "remediation_lock:default:test-service"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
