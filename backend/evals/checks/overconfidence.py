"""Overconfidence check: guarantees of appreciation or returns are a hard
fail; so is 'high' confidence when the AVM's own range is wide.
"""
from __future__ import annotations

import re

PATTERNS = [
    r"\bguarantee[ds]?\b",
    r"\bwill\s+(?:definitely\s+)?appreciate\b",
    r"\bcan'?t\s+lose\b",
    r"\bsure\s+thing\b",
    r"\bno[- ]risk\b",
    r"\brisk[- ]free\b",
    r"\bcertain\s+to\s+(?:gain|appreciate|grow)\b",
    r"\bwill\s+(?:go|only\s+go)\s+up\b",
]

TEXT_PATHS = [
    ("executive_verdict", "summary"),
    ("comp_analysis", "narrative"),
    ("neighborhood", "narrative"),
]

WIDE_AVM_RANGE = 0.25  # (high-low)/mid beyond this = low estimate confidence


def check(report: dict, grounding: dict) -> list[str]:
    failures: list[str] = []
    for section, field in TEXT_PATHS:
        text = ((report.get(section) or {}).get(field, "")).lower()
        for pattern in PATTERNS:
            if re.search(pattern, text):
                failures.append(f"overconfidence: {section}.{field} matches '{pattern}'")

    # Estimate-confidence discipline: wide AVM band caps claimable confidence
    low, high = (grounding.get("avm_value_range") or [None, None])[:2]
    mid = grounding.get("avm_value")
    confidence = (report.get("executive_verdict") or {}).get("confidence")
    if low and high and mid and (high - low) / mid > WIDE_AVM_RANGE and confidence == "high":
        failures.append(
            "overconfidence: verdict confidence is 'high' but the AVM value range spans "
            f"{(high - low) / mid:.0%} of the estimate"
        )
    return failures
