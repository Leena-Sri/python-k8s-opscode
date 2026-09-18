"""Redis cache layer implementation."""

import asyncio
import json
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.exceptions import RedisError as OpscodeRedisError

logger = get_logger(__name__)
settings = get_settings()

_redis_client: Redis | None = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global _redis_client

    logger.info("Initializing Redis connection", redis_url=settings.redis_url)

    _redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        max_connections=settings.redis_pool_size,
    )

    # Test connection
    try:
        await _redis_client.ping()
        logger.info("Redis connection established")
    except RedisError as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise OpscodeRedisError(f"Failed to connect to Redis: {e}")


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client

    if _redis_client:
        logger.info("Closing Redis connection")
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


def get_redis() -> Redis:
    """Get Redis client instance."""
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client


class RedisCache:
    """Redis cache wrapper with common operations."""

    def __init__(self, redis_client: Redis | None = None):
        """Initialize Redis cache."""
        self._client = redis_client or get_redis()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except RedisError as e:
            logger.warning("Redis get failed", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache with optional TTL."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            if ttl:
                await self._client.setex(key, ttl, value)
            else:
                await self._client.set(key, value)
            return True
        except RedisError as e:
            logger.warning("Redis set failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            await self._client.delete(key)
            return True
        except RedisError as e:
            logger.warning("Redis delete failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self._client.exists(key) > 0
        except RedisError as e:
            logger.warning("Redis exists check failed", key=key, error=str(e))
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        try:
            return await self._client.expire(key, ttl)
        except RedisError as e:
            logger.warning("Redis expire failed", key=key, error=str(e))
            return False

    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        try:
            return await self._client.ttl(key)
        except RedisError as e:
            logger.warning("Redis TTL check failed", key=key, error=str(e))
            return -1

    async def keys(self, pattern: str) -> list[str]:
        """Get keys matching pattern."""
        try:
            return await self._client.keys(pattern)
        except RedisError as e:
            logger.warning("Redis keys failed", pattern=pattern, error=str(e))
            return []

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        try:
            return await self._client.incrby(key, amount)
        except RedisError as e:
            logger.warning("Redis increment failed", key=key, error=str(e))
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter."""
        try:
            return await self._client.decrby(key, amount)
        except RedisError as e:
            logger.warning("Redis decrement failed", key=key, error=str(e))
            return 0


class DistributedLock:
    """Distributed lock using Redis."""

    def __init__(self, redis_client: Redis | None = None):
        """Initialize distributed lock."""
        self._client = redis_client or get_redis()

    async def acquire(
        self,
        lock_key: str,
        ttl: int = 30,
        wait_timeout: int = 10,
    ) -> bool:
        """Acquire lock with timeout."""
        import time

        start_time = time.time()
        while time.time() - start_time < wait_timeout:
            try:
                # Try to acquire lock using SET NX
                acquired = await self._client.set(
                    lock_key,
                    "locked",
                    nx=True,
                    ex=ttl,
                )
                if acquired:
                    logger.debug("Lock acquired", lock_key=lock_key)
                    return True
                # Wait before retrying
                await asyncio.sleep(0.1)
            except RedisError as e:
                logger.warning("Lock acquisition failed", lock_key=lock_key, error=str(e))
                return False
        logger.debug("Lock acquisition timed out", lock_key=lock_key)
        return False

    async def release(self, lock_key: str) -> bool:
        """Release lock."""
        try:
            await self._client.delete(lock_key)
            logger.debug("Lock released", lock_key=lock_key)
            return True
        except RedisError as e:
            logger.warning("Lock release failed", lock_key=lock_key, error=str(e))
            return False

    async def is_locked(self, lock_key: str) -> bool:
        """Check if lock is held."""
        try:
            return await self._client.exists(lock_key) > 0
        except RedisError as e:
            logger.warning("Lock check failed", lock_key=lock_key, error=str(e))
            return False


# Cache key generators
def workload_key(namespace: str, name: str) -> str:
    """Generate cache key for workload."""
    return f"workload:{namespace}:{name}"


def incident_key(incident_id: str) -> str:
    """Generate cache key for incident."""
    return f"incident:{incident_id}"


def remediation_lock_key(workload: str, namespace: str) -> str:
    """Generate cache key for remediation lock."""
    return f"remediation_lock:{namespace}:{workload}"


def cooldown_key(workload: str, namespace: str, action: str) -> str:
    """Generate cache key for remediation cooldown."""
    return f"cooldown:{namespace}:{workload}:{action}"


def health_check_key(workload: str, namespace: str) -> str:
    """Generate cache key for health check results."""
    return f"health:{namespace}:{workload}"
