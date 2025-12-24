"""
TTL Cache for Market Data

Simple in-memory cache with time-to-live expiration.
"""

import time
from typing import Any, Dict, Generic, Optional, TypeVar
from dataclasses import dataclass, field

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A cached value with expiration time."""

    value: T
    expires_at: float

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        return time.time() > self.expires_at


class TTLCache(Generic[T]):
    """
    Simple TTL-based cache.

    Usage:
        cache = TTLCache[ExchangeRates](default_ttl=300)  # 5 minute default
        cache.set("dawn-of-the-hunt", rates, ttl=600)  # 10 minute TTL
        rates = cache.get("dawn-of-the-hunt")  # Returns None if expired
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[T]:
        """
        Get a value from cache.

        Returns None if key doesn't exist or has expired.
        """
        entry = self._cache.get(key)
        if entry is None:
            return None

        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        if ttl is None:
            ttl = self._default_ttl

        expires_at = time.time() + ttl
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: str) -> bool:
        """Delete a key from cache. Returns True if key existed."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def cleanup(self) -> int:
        """
        Remove all expired entries.

        Returns the number of entries removed.
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def __len__(self) -> int:
        """Return number of non-expired entries."""
        self.cleanup()
        return len(self._cache)
