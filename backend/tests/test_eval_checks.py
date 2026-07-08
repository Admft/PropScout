"""The eval suite is itself the test: every fixture case must produce its
expected verdict, and the full regression suite must be green.
"""
from evals import cases
from evals.runner import run_evals, run_suite


def test_suite_is_green():
    result = run_suite()
    failing = [c for c in result["cases"] if not c["ok"]]
    assert not failing, f"eval suite regressions: {failing}"


def test_clean_base_case_passes_every_check():
    base = cases.build_base()
    result = run_evals(base["report"], base["grounding"])
    assert result["passed"], result["failures"]


def test_each_check_fires_independently():
    suite = {c["name"]: c for c in cases.all_cases()}
    # every named failure case actually fails for the reason it claims
    for name, case in suite.items():
        if case["expect_pass"]:
            continue
        result = run_evals(case["report"], case["grounding"])
        assert not result["passed"], f"{name} unexpectedly passed"
        needle = case.get("expect_failure_contains", "")
        assert any(needle in f for f in result["failures"]), (
            f"{name}: no failure contained '{needle}': {result['failures']}"
        )
