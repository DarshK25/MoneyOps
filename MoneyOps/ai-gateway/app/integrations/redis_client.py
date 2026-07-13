"""
Redis client for AI Gateway.
Uses Upstash (cloud) or local Redis depending on REDIS_TLS setting.
"""
import redis.asyncio as aioredis
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_redis_client: aioredis.Redis | None = None
_redis_failed: bool = False


async def get_redis() -> aioredis.Redis | None:
    """Get or create the Redis connection. Returns None if Redis is unavailable."""
    global _redis_client, _redis_failed
    if _redis_failed:
        return None
    if not settings.REDIS_HOST:
        return None
    if _redis_client is None:
        _redis_client = await _create_redis()
        if _redis_client is None:
            _redis_failed = True
    return _redis_client


async def _create_redis() -> aioredis.Redis | None:
    """Create a Redis connection (TLS for Upstash, plain for local)."""
    try:
        if settings.REDIS_TLS:
            url = (
                f"rediss://default:{settings.REDIS_PASSWORD}@"
                f"{settings.REDIS_HOST}:{settings.REDIS_PORT}"
            )
        else:
            if settings.REDIS_PASSWORD:
                url = (
                    f"redis://:{settings.REDIS_PASSWORD}@"
                    f"{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
                )
            else:
                url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

        client = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=0.5)
        await client.ping()
        logger.info("redis_connected", host=settings.REDIS_HOST, tls=settings.REDIS_TLS)
        return client

    except Exception as e:
        logger.warning("redis_unavailable", error=str(e), note="Continuing without cache")
        return None


async def close_redis():
    """Close the Redis connection on shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("redis_disconnected")


# ── Cache helpers ──────────────────────────────────────────────────────────────

async def cache_set(key: str, value: str, ttl_seconds: int = 300):
    """Set a cache key with expiry."""
    try:
        r = await get_redis()
        await r.setex(key, ttl_seconds, value)
    except Exception as e:
        logger.warning("cache_set_failed", key=key, error=str(e))


async def cache_get(key: str) -> str | None:
    """Get a cache key. Returns None on miss or error."""
    try:
        r = await get_redis()
        return await r.get(key)
    except Exception as e:
        logger.warning("cache_get_failed", key=key, error=str(e))
        return None


async def cache_delete(key: str):
    """Delete a cache key."""
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception as e:
        logger.warning("cache_delete_failed", key=key, error=str(e))
