"""Redis cache with in-memory fallback so local dev works without Redis.
Provider API responses are cached because RentCast/ATTOM calls are metered.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None
_redis_failed = False
_memory: dict[str, tuple[float, str]] = {}


def _get_client() -> Optional[redis.Redis]:
    global _client, _redis_failed
    if _redis_failed:
        return None
    if _client is None:
        try:
            _client = redis.Redis.from_url(
                get_settings().redis_url, socket_connect_timeout=1, decode_responses=True
            )
            _client.ping()
        except Exception:
            logger.warning("Redis unavailable; falling back to in-memory cache")
            _redis_failed = True
            _client = None
    return _client


def cache_get(key: str) -> Optional[Any]:
    client = _get_client()
    if client:
        try:
            raw = client.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None
    entry = _memory.get(key)
    if entry and entry[0] > time.time():
        return json.loads(entry[1])
    _memory.pop(key, None)
    return None


def cache_set(key: str, value: Any, ttl: int) -> None:
    raw = json.dumps(value, default=str)
    client = _get_client()
    if client:
        try:
            client.setex(key, ttl, raw)
            return
        except Exception:
            pass
    _memory[key] = (time.time() + ttl, raw)
