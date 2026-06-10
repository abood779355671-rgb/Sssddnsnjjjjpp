import time
import asyncio
import json
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class MemoryCache:
    """LRU memory cache as Redis fallback."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        async with self._lock:
            expires_at = time.time() + ttl
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (value, expires_at)
            return True

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._cache:
                return None
            value, expires_at = self._cache[key]
            if time.time() > expires_at:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return value

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        val = await self.get(key)
        return val is not None

    async def clear_expired(self):
        async with self._lock:
            now = time.time()
            expired = [k for k, (_, exp) in self._cache.items() if now > exp]
            for k in expired:
                del self._cache[k]

    def size(self) -> int:
        return len(self._cache)


# Global fallback memory cache
memory_cache = MemoryCache(max_size=500)


async def get_from_any_cache(key: str, redis_get_fn=None) -> Optional[Any]:
    """Try Redis first, fallback to memory cache."""
    from bot.cache.redis_cache import get_cache
    value = await get_cache(key)
    if value is not None:
        return value
    return await memory_cache.get(key)


async def set_to_any_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set to Redis first, always set to memory cache as backup."""
    from bot.cache.redis_cache import set_cache
    await memory_cache.set(key, value, ttl)
    return await set_cache(key, value, ttl)
