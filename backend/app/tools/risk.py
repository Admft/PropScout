"""Objective risk flags assembled from FEMA data and property facts.
Each flag carries the source it came from; severity rules are deterministic.
"""
from __future__ import annotations

from datetime import date
from typing import Optional


def build_risk_flags(
    flood: Optional[dict],
    year_built: Optional[int],
    annual_taxes: Optional[float],
    purchase_price: Optional[float],
) -> list[dict]:
    flags: list[dict] = []

    if flood is None or flood.get("high_risk") is None:
        flags.append(
            {
                "category": "flood",
                "severity": "unknown",
                "detail": "Flood zone could not be determined from FEMA NFHL for this location.",
                "source_ids": ["fema:flood"],
            }
        )
    elif flood.get("high_risk"):
        flags.append(
            {
                "category": "flood",
                "severity": "high",
                "detail": (
                    f"Property falls in FEMA zone {flood.get('zone')}, a Special Flood Hazard "
                    "Area. Flood insurance is typically required for federally backed mortgages."
                ),
                "source_ids": ["fema:flood"],
            }
        )
    else:
        flags.append(
            {
                "category": "flood",
                "severity": "low",
                "detail": f"FEMA zone {flood.get('zone')}: outside the high-risk flood area.",
                "source_ids": ["fema:flood"],
            }
        )

    if year_built:
        age = date.today().year - year_built
        if age >= 50:
            flags.append(
                {
                    "category": "maintenance",
                    "severity": "high",
                    "detail": (
                        f"Built in {year_built} ({age} years old). Original-era roof, plumbing, "
                        "and electrical systems are likely past service life; budget for inspection findings."
                    ),
                    "source_ids": ["rentcast:property"],
                }
            )
        elif age >= 25:
            flags.append(
                {
                    "category": "maintenance",
                    "severity": "moderate",
                    "detail": (
                        f"Built in {year_built} ({age} years old). Major systems (roof, HVAC, "
                        "water heater) may be approaching replacement windows."
                    ),
                    "source_ids": ["rentcast:property"],
                }
            )

    if annual_taxes and purchase_price and purchase_price > 0:
        effective_rate = annual_taxes / purchase_price
        if effective_rate >= 0.02:
            flags.append(
                {
                    "category": "taxes",
                    "severity": "moderate",
                    "detail": (
                        f"Effective property tax rate is {effective_rate:.1%} of the purchase "
                        "price, above the ~1.1% national average; verify post-sale reassessment rules."
                    ),
                    "source_ids": ["rentcast:property"],
                }
            )

    return flags
