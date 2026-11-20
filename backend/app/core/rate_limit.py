"""Tiny in-process rate limiter for login and AI endpoints.

The local demo is single-process. In a multi-process deployment this would move
to Redis or a database-backed limiter; the interface stays the same.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from app.core.errors import ApiError


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, code: str = "rate_limited") -> None:
        now = time.monotonic()
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= now - self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.limit:
                raise ApiError(
                    code,
                    "Too many requests. Please wait and try again.",
                    429,
                )
            bucket.append(now)

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._events.clear()
            else:
                self._events.pop(key, None)


login_limiter = RateLimiter(limit=8, window_seconds=15 * 60)
ai_limiter = RateLimiter(limit=20, window_seconds=60 * 60)
