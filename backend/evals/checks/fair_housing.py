"""Fair-housing language check: steering or demographic-coded phrasing in any
narrative text is a hard fail. Pattern list is deliberately broad — a human
reviews flagged reports rather than shipping them.
"""
from __future__ import annotations

import re

PATTERNS = [
    (r"\bgood\s+(?:for\s+)?famil(?:y|ies)\b", "family steering"),
    (r"\bfamily[- ]friendly\b", "family steering"),
    (r"\bsafe\s+neighborhood\b", "coded safety claim"),
    (r"\b(?:low|high)[- ]crime\b", "crime characterization"),
    (r"\bdesirable\s+(?:neighborhood|area|community)\b", "desirability steering"),
    (r"\b(?:changing|transitional|up[- ]and[- ]coming)\s+(?:neighborhood|area)\b", "coded turnover language"),
    (r"\bkind\s+of\s+people\b", "demographic phrasing"),
    (r"\b(?:white|black|hispanic|latino|asian|jewish|muslim|christian)\s+(?:neighborhood|area|community)\b", "explicit demographic reference"),
    (r"\bethnic\b", "demographic phrasing"),
    (r"\bdemographic(?:s)?\s+(?:are|is)\s+(?:improving|declining)\b", "demographic trend claim"),
    (r"\bgood\s+schools?\b", "school-quality proxy steering"),
    (r"\bimmigrant\b", "national-origin phrasing"),
]

TEXT_PATHS = [
    ("executive_verdict", "summary"),
    ("executive_verdict", "best_fit_buyer"),
    ("executive_verdict", "worst_fit_buyer"),
    ("comp_analysis", "narrative"),
    ("neighborhood", "narrative"),
]


def check(report: dict, grounding: dict) -> list[str]:
    failures: list[str] = []
    texts = [((s, f), (report.get(s) or {}).get(f, "")) for s, f in TEXT_PATHS]
    texts += [(("questions_to_ask", str(i)), q) for i, q in enumerate(report.get("questions_to_ask", []))]

    for (section, field), text in texts:
        lowered = text.lower()
        for pattern, label in PATTERNS:
            if re.search(pattern, lowered):
                failures.append(f"fair-housing: {section}.{field} contains {label} ({pattern})")
    return failures
