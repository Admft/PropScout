"""Comp selection and pricing analysis from RentCast AVM comparables.
Filtering rules mirror the eval harness's comp-quality check: distance,
size band, recency, and matching property type.
"""
from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.tools.calculators import price_per_sqft


def _months_since(date_str: Optional[str]) -> Optional[float]:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None
    now = datetime.now(timezone.utc)
    return (now - dt).days / 30.44


def select_comps(
    raw_comps: list[dict],
    subject_sqft: Optional[float],
    subject_type: Optional[str],
    max_results: int = 6,
) -> list[dict]:
    settings = get_settings()
    selected = []
    for c in raw_comps:
        distance = c.get("distance")
        sqft = c.get("squareFootage")
        months = _months_since(c.get("removedDate") or c.get("listedDate"))
        if distance is not None and distance > settings.comp_max_distance_miles:
            continue
        if subject_sqft and sqft:
            if abs(sqft - subject_sqft) / subject_sqft > settings.comp_sqft_band:
                continue
        if subject_type and c.get("propertyType") and c["propertyType"] != subject_type:
            continue
        if months is not None and months > settings.comp_max_age_months:
            continue
        price = c.get("price")
        selected.append(
            {
                "address": c.get("formattedAddress") or c.get("addressLine1") or "Unknown",
                "distance_miles": round(distance, 2) if distance is not None else None,
                "sale_price": price,
                "sale_date": (c.get("removedDate") or c.get("listedDate") or "")[:10] or None,
                "bedrooms": c.get("bedrooms"),
                "bathrooms": c.get("bathrooms"),
                "square_footage": sqft,
                "price_per_sqft": price_per_sqft(price, sqft),
            }
        )
    selected.sort(key=lambda c: (c["distance_miles"] is None, c["distance_miles"]))
    return selected[:max_results]


def analyze_pricing(
    comps: list[dict], purchase_price: Optional[float], subject_sqft: Optional[float]
) -> dict:
    ppsf_values = [c["price_per_sqft"] for c in comps if c.get("price_per_sqft")]
    median_ppsf = round(statistics.median(ppsf_values), 2) if ppsf_values else None
    subject_ppsf = price_per_sqft(purchase_price, subject_sqft)
    delta = None
    if subject_ppsf and median_ppsf:
        delta = round((subject_ppsf - median_ppsf) / median_ppsf * 100, 1)
    return {
        "comps": comps,
        "subject_price_per_sqft": subject_ppsf,
        "median_comp_price_per_sqft": median_ppsf,
        "pricing_delta_pct": delta,
    }
