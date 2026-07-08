"""Eval harness entry points.

- run_evals(report, grounding): the pre-ship gate every generated report passes
  through before it is returned to a user.
- run_suite(): the offline regression suite over fixture cases; run in CI and
  via POST /evals/run.
"""
from __future__ import annotations

from evals.checks import (
    comp_quality,
    fair_housing,
    math_correctness,
    overconfidence,
    source_usage,
    tool_discipline,
)

CHECKS = [
    ("math_correctness", math_correctness.check),
    ("source_usage", source_usage.check),
    ("tool_discipline", tool_discipline.check),
    ("comp_quality", comp_quality.check),
    ("fair_housing", fair_housing.check),
    ("overconfidence", overconfidence.check),
]


def run_evals(report: dict, grounding: dict) -> dict:
    failures: list[str] = []
    results: dict[str, list[str]] = {}
    for name, fn in CHECKS:
        found = fn(report, grounding)
        results[name] = found
        failures.extend(found)
    return {"passed": not failures, "failures": failures, "results": results}


def run_suite() -> dict:
    from evals import cases

    outcomes = []
    for case in cases.all_cases():
        result = run_evals(case["report"], case["grounding"])
        expected_pass = case["expect_pass"]
        ok = result["passed"] == expected_pass
        if ok and not expected_pass:
            needle = case.get("expect_failure_contains")
            if needle:
                ok = any(needle in f for f in result["failures"])
        outcomes.append(
            {
                "name": case["name"],
                "ok": ok,
                "expected_pass": expected_pass,
                "actual_pass": result["passed"],
                "failures": result["failures"],
            }
        )
    passed = sum(1 for o in outcomes if o["ok"])
    return {
        "total": len(outcomes),
        "passed": passed,
        "failed": len(outcomes) - passed,
        "cases": outcomes,
    }
