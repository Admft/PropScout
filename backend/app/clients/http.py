from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

import httpx

from app.cache import cache_get, cache_set
from app.config import get_settings

logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(20.0)


def cached_get_json(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    cache_prefix: str,
    ttl: Optional[int] = None,
) -> Any:
    """GET with Redis caching. Returns parsed JSON, or None on any failure —
    callers must degrade gracefully and mark the section's data as missing.
    """
    key_body = json.dumps({"u": url, "p": params}, sort_keys=True)
    key = f"{cache_prefix}:{hashlib.sha256(key_body.encode()).hexdigest()[:24]}"
    cached = cache_get(key)
    if cached is not None:
        return cached
    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("GET %s failed: %s", url, exc)
        return None
    cache_set(key, data, ttl or get_settings().provider_cache_ttl)
    return data
