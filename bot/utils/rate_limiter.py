import time
import asyncio
from collections import defaultdict
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter using sliding window."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: Dict[int, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, user_id: int) -> Tuple[bool, int]:
        """Check if user is within rate limit. Returns (allowed, wait_seconds)."""
        async with self._lock:
            now = time.time()
            user_requests = self._requests[user_id]
            # Remove expired entries
            self._requests[user_id] = [t for t in user_requests if now - t < self.window]
            if len(self._requests[user_id]) < self.max_requests:
                self._requests[user_id].append(now)
                return True, 0
            oldest = self._requests[user_id][0]
            wait = int(self.window - (now - oldest)) + 1
            return False, wait

    async def reset(self, user_id: int):
        async with self._lock:
            self._requests.pop(user_id, None)


class DownloadCooldown:
    """Cooldown between downloads per user."""

    def __init__(self, cooldown_seconds: int):
        self.cooldown = cooldown_seconds
        self._last_download: Dict[int, float] = {}
        self._lock = asyncio.Lock()

    async def can_download(self, user_id: int) -> Tuple[bool, int]:
        async with self._lock:
            now = time.time()
            last = self._last_download.get(user_id, 0)
            elapsed = now - last
            if elapsed >= self.cooldown:
                self._last_download[user_id] = now
                return True, 0
            wait = int(self.cooldown - elapsed) + 1
            return False, wait

    async def reset(self, user_id: int):
        async with self._lock:
            self._last_download.pop(user_id, None)


class FloodControl:
    """Anti-flood control."""

    def __init__(self, max_warnings: int = 3, ban_duration: int = 300):
        self.max_warnings = max_warnings
        self.ban_duration = ban_duration
        self._warnings: Dict[int, int] = defaultdict(int)
        self._banned_until: Dict[int, float] = {}
        self._lock = asyncio.Lock()

    async def check(self, user_id: int) -> Tuple[bool, int]:
        """Returns (is_banned, seconds_remaining)."""
        async with self._lock:
            now = time.time()
            if user_id in self._banned_until:
                remaining = self._banned_until[user_id] - now
                if remaining > 0:
                    return True, int(remaining)
                else:
                    del self._banned_until[user_id]
                    self._warnings[user_id] = 0
            return False, 0

    async def warn(self, user_id: int):
        async with self._lock:
            self._warnings[user_id] += 1
            if self._warnings[user_id] >= self.max_warnings:
                self._banned_until[user_id] = time.time() + self.ban_duration
                self._warnings[user_id] = 0
