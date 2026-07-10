"""

Redis cache wrapper with simple fallback for local dev.
"""
import os
import json
import logging
from typing import Optional, Any

logger = logging.getLogger('app.redis')

_REDIS_URL = os.getenv('REDIS_URL')
_client = None
_FallbackMap = {}

def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import redis as redis_module
        _client = redis_module.from_url(_REDIS_URL or 'redis://localhost:6379/0', decode_responses=True)
        _client.ping()
        logger.info('Redis connected')
        return _client
    except Exception as e:
        logger.warning('Redis unavailable, using in-memory fallback: %s', e)
        _FallbackMap.clear()
        _client = None
        return None

def get(key: str) -> Optional[Any]:
    client = _get_client()
    if client is not None:
        raw = client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw
    return _FallbackMap.get(key)

def set(key: str, value: Any, ttl: int = 300) -> None:
    client = _get_client()
    if client is not None:
        try:
            raw = value if isinstance(value, str) else json.dumps(value)
            client.setex(key, ttl, raw)
            return
        except Exception as e:
            logger.warning('Redis set failed, fallback: %s', e)
    _FallbackMap[key] = value

def delete(key: str) -> None:
    client = _get_client()
    if client is not None:
        try:
            client.delete(key)
            return
        except Exception:
            pass
    _FallbackMap.pop(key, None)
