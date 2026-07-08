"""Unsupported claims + tool discipline: every dollar figure, percentage, and
large number in the narrative must trace back to grounding data or a recorded
tool result. A number with no provenance means the model computed or invented
it instead of calling a tool.
"""
from __future__ import annotations

import re

NUMBER_RE = re.compile(r"\$?([\d,]+(?:\.\d+)?)\s*(%|k\b|K\b)?")

NARRATIVE_PATHS = [
    ("executive_verdict", "summary"),
    ("comp_analysis", "narrative"),
    ("neighborhood", "narrative"),
]

# Small integers in prose ("3 bedrooms", "two of the six comps") aren't claims
MIN_SIGNIFICANT = 50


def _collect_grounded_numbers(node, out: set) -> None:
    if isinstance(node, dict):
        for v in node.values():
            _collect_grounded_numbers(v, out)
    elif isinstance(node, list):
        for v in node:
            _collect_grounded_numbers(v, out)
    elif isinstance(node, bool):
        return
    elif isinstance(node, (int, float)):
        out.add(round(float(node), 2))
        # ratios are usually narrated as percentages
        if 0 < abs(node) < 1:
            out.add(round(float(node) * 100, 2))


def _narrated_numbers(text: str) -> list[float]:
    values = []
    for raw, suffix in NUMBER_RE.findall(text):
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        if suffix in ("k", "K"):
            value *= 1000
        # years read as numbers aren't financial claims
        if 1900 <= value <= 2100 and "." not in raw:
            continue
        if abs(value) < MIN_SIGNIFICANT and suffix != "%":
            continue
        values.append(round(value, 2))
    return values


def _is_grounded(value: float, grounded: set) -> bool:
    for g in grounded:
        if g == 0:
            continue
        if abs(value - g) <= max(abs(g) * 0.005, 0.5):  # tolerate narration rounding
            return True
        # "$450k" / "roughly 450,000" style rounding to 2 significant figures
        if abs(value) >= 1000 and abs(value - round(g, -3)) <= 0.5:
            return True
    return False


def check(report: dict, grounding: dict) -> list[str]:
    grounded: set = set()
    _collect_grounded_numbers(grounding, grounded)
    _collect_grounded_numbers(report.get("tool_calls", []), grounded)
    _collect_grounded_numbers(report.get("payment_model") or {}, grounded)
    _collect_grounded_numbers(report.get("investment_model") or {}, grounded)
    _collect_grounded_numbers(report.get("comp_analysis") or {}, grounded)

    failures: list[str] = []
    for section, field in NARRATIVE_PATHS:
        text = (report.get(section) or {}).get(field, "")
        for value in _narrated_numbers(text):
            if not _is_grounded(value, grounded):
                failures.append(
                    f"tool-discipline: {section}.{field} states {value} which matches no "
                    "grounding data or tool result"
                )
    return failures
