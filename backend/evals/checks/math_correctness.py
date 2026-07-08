"""Recompute every financial model in the report from its own inputs and
fail if any figure drifts. Catches both calculator regressions and any path
where a number was edited after the tools ran.
"""
from __future__ import annotations

from app.tools import calculators

TOLERANCE = 0.01  # dollars/ratio absolute drift allowed from rounding


def check(report: dict, grounding: dict) -> list[str]:
    failures: list[str] = []

    pm = report.get("payment_model")
    if pm:
        expected = calculators.calculate_payment_model(
            pm["purchase_price"],
            pm["down_payment_pct"],
            pm["annual_rate"],
            pm["term_years"],
            pm["monthly_taxes"] * 12,
            pm["monthly_insurance"] * 12,
        )
        for field in ("down_payment", "loan_amount", "monthly_principal_interest", "all_in_monthly"):
            if abs(expected[field] - pm[field]) > TOLERANCE:
                failures.append(
                    f"math: payment_model.{field} is {pm[field]}, recomputed {expected[field]}"
                )

    im = report.get("investment_model")
    if im:
        expected_cap = calculators.calculate_cap_rate(
            im["noi_annual"], pm["purchase_price"] if pm else 0
        )
        if abs(expected_cap - im["cap_rate"]) > 0.0005:
            failures.append(f"math: cap_rate is {im['cap_rate']}, recomputed {expected_cap}")
        if pm:
            expected_cf = calculators.calculate_cash_flow(
                im["noi_annual"], pm["monthly_principal_interest"]
            )
            if abs(expected_cf - im["monthly_cash_flow"]) > TOLERANCE:
                failures.append(
                    f"math: monthly_cash_flow is {im['monthly_cash_flow']}, recomputed {expected_cf}"
                )
        expected_coc = calculators.calculate_cash_on_cash(
            im["monthly_cash_flow"] * 12, im["cash_invested"]
        )
        if abs(expected_coc - im["cash_on_cash_return"]) > 0.0005:
            failures.append(
                f"math: cash_on_cash_return is {im['cash_on_cash_return']}, recomputed {expected_coc}"
            )

    return failures
