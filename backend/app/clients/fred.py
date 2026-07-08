"""FRED: current 30-year fixed mortgage rate (series MORTGAGE30US) used as
the default rate assumption. Falls back to the configured default without a key.
"""
from __future__ import annotations

from typing import Optional

from app.clients.http import cached_get_json
from app.config import get_settings


def get_mortgage_rate() -> Optional[dict]:
    settings = get_settings()
    if not settings.fred_api_key:
        return None
    data = cached_get_json(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id": "MORTGAGE30US",
            "api_key": settings.fred_api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        },
        cache_prefix="fred:mortgage30us",
        ttl=60 * 60 * 24,
    )
    try:
        obs = data["observations"][0]
        return {"rate": float(obs["value"]) / 100, "as_of": obs["date"]}
    except (TypeError, KeyError, IndexError, ValueError):
        return None
