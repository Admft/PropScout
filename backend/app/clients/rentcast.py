"""RentCast: property facts, value/rent estimates, and comps.
Docs: https://developers.rentcast.io/reference
"""
from __future__ import annotations

from typing import Optional

from app.clients.http import cached_get_json
from app.config import get_settings

BASE = "https://api.rentcast.io/v1"


def _headers() -> dict:
    return {"X-Api-Key": get_settings().rentcast_api_key, "Accept": "application/json"}


def get_property(address: str) -> Optional[dict]:
    data = cached_get_json(
        f"{BASE}/properties",
        params={"address": address},
        headers=_headers(),
        cache_prefix="rentcast:property",
    )
    if isinstance(data, list):
        return data[0] if data else None
    return data


def get_value_estimate(address: str) -> Optional[dict]:
    """AVM value estimate with comparables — the comp source for reports."""
    return cached_get_json(
        f"{BASE}/avm/value",
        params={"address": address, "compCount": 10},
        headers=_headers(),
        cache_prefix="rentcast:avm-value",
    )


def get_rent_estimate(address: str) -> Optional[dict]:
    return cached_get_json(
        f"{BASE}/avm/rent/long-term",
        params={"address": address, "compCount": 10},
        headers=_headers(),
        cache_prefix="rentcast:avm-rent",
    )
