"""
app/core/cache.py
─────────────────
Simple in-memory TTL cache.  Drop-in replaceable with a Redis backend
by swapping the ICache implementation injected into services.
"""

import time
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class ICache:
    """Abstract cache interface."""

    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int) -> None:
        raise NotImplementedError

    def invalidate(self, key: str) -> None:
        raise NotImplementedError


class InMemoryCache(ICache):
    """Thread-safe in-memory TTL cache."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = (value, time.monotonic() + ttl)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def cached(self, key: str, ttl: int, loader: Callable[[], T]) -> T:
        """Return cached value or call loader() and cache the result."""
        hit = self.get(key)
        if hit is not None:
            return hit  # type: ignore[return-value]
        value = loader()
        self.set(key, value, ttl)
        return value


# Singleton — shared across all services in a process
_cache = InMemoryCache()


def get_cache() -> InMemoryCache:
    return _cache
