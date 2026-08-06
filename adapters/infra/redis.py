"""Redis adapter — implements CacheAdapter for in-memory caching.

Uses redis-py when the Redis server is available.
Falls back to an in-process dict when no server is present.
"""

from __future__ import annotations

from typing import Any

from adapters import CacheAdapter


class RedisCacheAdapter(CacheAdapter):
    """Cache via Redis — in-memory key-value with optional TTL."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._local: dict[str, tuple[Any, float]] = {}  # fallback: key -> (value, expire_ts)
        self._redis = None  # lazy import
        self._connected = False

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    def connect(self) -> bool:
        """Attempt real Redis connection; fall back to local dict on failure."""
        try:
            import redis  # type: ignore[import-untyped]

            pool = redis.ConnectionPool(
                host=self._host, port=self._port, db=self._db, decode_responses=True
            )
            self._redis = redis.Redis(connection_pool=pool)
            self._redis.ping()
            self._connected = True
        except Exception:
            self._connected = False
            self._redis = None
        return self._connected

    # ------------------------------------------------------------------
    # CacheAdapter interface
    # ------------------------------------------------------------------
    def get(self, key: str) -> Any:
        if self._connected and self._redis is not None:
            try:
                return self._redis.get(key)
            except Exception:
                self._connected = False

        # Local fallback
        import time

        entry = self._local.get(key)
        if entry is None:
            return None
        value, expire = entry
        if expire > 0 and time.monotonic() > expire:
            del self._local[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if self._connected and self._redis is not None:
            try:
                self._redis.setex(key, ttl, value)
                return True
            except Exception:
                self._connected = False

        # Local fallback
        import time

        expire = (time.monotonic() + ttl) if ttl > 0 else 0.0
        self._local[key] = (value, expire)
        return True

    def delete(self, key: str) -> bool:
        if self._connected and self._redis is not None:
            try:
                return bool(self._redis.delete(key))
            except Exception:
                self._connected = False

        return bool(self._local.pop(key, None))

    # ------------------------------------------------------------------
    # Redis-specific extras
    # ------------------------------------------------------------------
    def flush(self) -> bool:
        """Flush all keys (dev/test only)."""
        if self._connected and self._redis is not None:
            try:
                self._redis.flushdb()
                return True
            except Exception:
                self._connected = False
        self._local.clear()
        return True

    def __repr__(self) -> str:
        return (
            f"RedisCacheAdapter(host={self._host}, port={self._port}, "
            f"connected={self._connected})"
        )