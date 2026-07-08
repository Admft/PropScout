"""Comp quality: comps in a shipped report must be near, similar, and recent.
Bounds mirror app.config so the selector and the police agree.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_settings


def check(report: dict, grounding: dict) -> list[str]:
    settings = get_settings()
    failures: list[str] = []
    subject_sqft = (report.get("property_facts") or {}).get("square_footage")
    comps = (report.get("comp_analysis") or {}).get("comps") or []

    if not comps:
        failures.append("comps: report contains no comparables")
        return failures

    for c in comps:
        label = c.get("address", "comp")
        dist = c.get("distance_miles")
        if dist is not None and dist > settings.comp_max_distance_miles:
            failures.append(f"comps: {label} is {dist} mi away (max {settings.comp_max_distance_miles})")
        sqft = c.get("square_footage")
        if subject_sqft and sqft:
            drift = abs(sqft - subject_sqft) / subject_sqft
            if drift > settings.comp_sqft_band:
                failures.append(
                    f"comps: {label} is {sqft} sqft vs subject {subject_sqft} "
                    f"({drift:.0%} outside the ±{settings.comp_sqft_band:.0%} band)"
                )
        sale_date = c.get("sale_date")
        if sale_date:
            try:
                dt = datetime.fromisoformat(sale_date).replace(tzinfo=timezone.utc)
                months = (datetime.now(timezone.utc) - dt).days / 30.44
                if months > settings.comp_max_age_months:
                    failures.append(
                        f"comps: {label} sold {months:.0f} months ago (max {settings.comp_max_age_months})"
                    )
            except ValueError:
                pass
    return failures
