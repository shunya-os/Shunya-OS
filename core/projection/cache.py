"""Projection Cache — TTL-based caching with event-driven invalidation."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .types import GraphProjection


@dataclass
class CacheEntry:
    """A single cached projection entry."""

    key: str
    projection: GraphProjection
    expires_at: datetime
    invalidated: bool = False

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.invalidated and not self.is_expired


@dataclass
class CacheStats:
    """Statistics for cache monitoring."""

    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    evictions: int = 0
    expired_collected: int = 0
    size: int = 0


class ProjectionCache:
    """Thread-safe TTL-based cache for GraphProjections.

    Supports event-driven invalidation by projection type and/or root node.
    Expired entries are lazily collected on read.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: dict[str, CacheEntry] = {}
        self._stats = CacheStats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> GraphProjection | None:
        """Retrieve a cached projection by key.

        Returns None if the entry does not exist, is expired, or has
        been invalidated. Expired entries are lazily removed on read.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._stats.misses += 1
                self._stats.size = len(self._entries)
                return None
            if not entry.is_valid:
                if entry.is_expired:
                    self._stats.expired_collected += 1
                del self._entries[key]
                self._stats.misses += 1
                self._stats.size = len(self._entries)
                return None
            self._stats.hits += 1
            self._stats.size = len(self._entries)
            return entry.projection

    def set(
        self,
        key: str,
        projection: GraphProjection,
        ttl_seconds: float,
    ) -> None:
        """Store a projection with the given TTL.

        A TTL of 0 or less means no caching (entry is not stored).
        """
        if ttl_seconds <= 0:
            return
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        with self._lock:
            self._entries[key] = CacheEntry(
                key=key,
                projection=projection,
                expires_at=expires_at,
            )
            self._stats.size = len(self._entries)

    def invalidate(self, projection_type: str | None = None, root_id: str | None = None) -> int:
        """Invalidate cache entries matching the given criteria.

        Args:
            projection_type: If set, only invalidate entries of this type.
            root_id: If set, only invalidate entries whose key contains root_id.

        Returns the number of entries invalidated.
        """
        count = 0
        with self._lock:
            for key, entry in list(self._entries.items()):
                matches_type = projection_type is None or entry.projection.projection_type == projection_type
                matches_root = root_id is None or root_id in key
                if matches_type and matches_root:
                    entry.invalidated = True
                    count += 1
            self._stats.invalidations += count
            self._stats.size = len(self._entries)
        return count

    def evict_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns the number of entries removed.
        """
        count = 0
        with self._lock:
            keys = list(self._entries.keys())
            for key in keys:
                entry = self._entries.get(key)
                if entry and entry.is_expired:
                    del self._entries[key]
                    count += 1
            self._stats.evictions += count
            self._stats.expired_collected += count
            self._stats.size = len(self._entries)
        return count

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            self._stats.evictions += count
            self._stats.size = 0

    def build_key(self, projection_type: str, root_id: str, query_hash: str = "") -> str:
        """Build a canonical cache key.

        Format: ``projection_type:root_id[:query_hash]``
        """
        if query_hash:
            return f"{projection_type}:{root_id}:{query_hash}"
        return f"{projection_type}:{root_id}"

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        """Return current cache statistics."""
        with self._lock:
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "invalidations": self._stats.invalidations,
                "evictions": self._stats.evictions,
                "expired_collected": self._stats.expired_collected,
                "size": self._stats.size,
                "hit_rate": round(
                    self._stats.hits / max(self._stats.hits + self._stats.misses, 1), 4
                ),
            }

    def health_check(self) -> dict[str, Any]:
        """Return cache health status."""
        s = self.stats()
        return {
            "status": "healthy",
            "component": "projection_cache",
            "size": s["size"],
            "hit_rate": s["hit_rate"],
            "invalidations": s["invalidations"],
        }


__all__ = [
    "CacheEntry",
    "CacheStats",
    "ProjectionCache",
]