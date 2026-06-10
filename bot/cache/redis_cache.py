import json
import logging
import asyncio
from typing import Any, Optional
import redis.asyncio as aioredis
from bot.config import config

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def init_redis() -> Optional[aioredis.Redis]:
    global _redis
    try:
        _redis = aioredis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            password=config.REDIS_PASSWORD or None,
            db=config.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            max_connections=20,
        )
        await _redis.ping()
        logger.info("Redis connected successfully.")
        return _redis
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Using memory cache fallback.")
        _redis = None
        return None


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        logger.info("Redis connection closed.")


async def get_redis() -> Optional[aioredis.Redis]:
    return _redis


async def ping_redis() -> bool:
    if not _redis:
        return False
    try:
        return await _redis.ping()
    except Exception:
        return False


async def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    if not _redis:
        return False
    try:
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        await _redis.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.warning(f"Redis set error: {e}")
        return False


async def get_cache(key: str) -> Optional[Any]:
    if not _redis:
        return None
    try:
        raw = await _redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Redis get error: {e}")
        return None


async def delete_cache(key: str) -> bool:
    if not _redis:
        return False
    try:
        await _redis.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Redis delete error: {e}")
        return False


async def exists_cache(key: str) -> bool:
    if not _redis:
        return False
    try:
        return bool(await _redis.exists(key))
    except Exception:
        return False


async def increment(key: str, ttl: int = 60) -> int:
    if not _redis:
        return 0
    try:
        val = await _redis.incr(key)
        if val == 1:
            await _redis.expire(key, ttl)
        return val
    except Exception:
        return 0
