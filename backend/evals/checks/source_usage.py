"""Citation presence: every narrative section must cite at least one source
id that actually exists in the report's source list.
"""
from __future__ import annotations

import re

CITATION_RE = re.compile(r"\[([a-z0-9:_\-]+)\]")

NARRATIVE_PATHS = [
    ("executive_verdict", "summary"),
    ("comp_analysis", "narrative"),
    ("neighborhood", "narrative"),
]


def check(report: dict, grounding: dict) -> list[str]:
    failures: list[str] = []
    valid_ids = {s["id"] for s in report.get("sources", [])}
    valid_ids |= {f"tool:{tc['tool']}" for tc in report.get("tool_calls", [])}

    for section, field in NARRATIVE_PATHS:
        text = (report.get(section) or {}).get(field, "")
        cited = set(CITATION_RE.findall(text))
        if not cited:
            failures.append(f"citations: {section}.{field} cites no sources")
            continue
        unknown = cited - valid_ids
        if unknown:
            failures.append(
                f"citations: {section}.{field} cites unknown source(s): {sorted(unknown)}"
            )
    return failures
