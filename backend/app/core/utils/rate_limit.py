import re
from datetime import UTC, datetime
from typing import Optional

from fastapi import Request
from redis.asyncio import ConnectionPool, Redis

from app.core.exceptions import RateLimitException
from app.core.logger import logging

logger = logging.getLogger(__name__)


def sanitize_path(path: str) -> str:
    """Sanitize path by replacing UUIDs with a placeholder."""
    return re.sub(r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "/{uuid}", path)


class RateLimiter:
    _instance: Optional["RateLimiter"] = None
    pool: Optional[ConnectionPool] = None
    client: Optional[Redis] = None

    def __new__(cls) -> "RateLimiter":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, redis_url: str) -> None:
        instance = cls()
        if instance.pool is None:
            instance.pool = ConnectionPool.from_url(redis_url)
            instance.client = Redis(connection_pool=instance.pool)

    @classmethod
    def get_client(cls) -> Redis:
        instance = cls()
        if instance.client is None:
            logger.error("Redis client is not initialized.")
            raise Exception("Redis client is not initialized.")
        return instance.client

    async def is_rate_limited(self, key: str, limit: int, period: int) -> bool:
        if self.client is None:
            return False

        client = self.client
        try:
            current_count = await client.incr(key)
            if current_count == 1:
                await client.expire(key, period)

            if current_count > limit:
                return True

        except Exception as e:
            logger.exception(f"Error checking rate limit for key {key}: {e}")

        return False


rate_limiter = RateLimiter()


class RateLimit:
    def __init__(self, limit: int, period: int):
        self.limit = limit
        self.period = period

    async def __call__(self, request: Request) -> None:
        # Use IP + Sanitized Path + Window Start as the key
        ip = request.client.host if request.client else "unknown"
        path = sanitize_path(request.url.path)

        current_timestamp = int(datetime.now(UTC).timestamp())
        window_start = current_timestamp - (current_timestamp % self.period)
        key = f"ratelimit:{ip}:{path}:{window_start}"

        if await rate_limiter.is_rate_limited(key, self.limit, self.period):
            raise RateLimitException("Rate limit exceeded.")
