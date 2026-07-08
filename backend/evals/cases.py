"""Eval fixture cases. The base case is built with the real calculators so
its math is correct by construction; each failure case mutates one thing the
harness must catch. Grow this toward the 30-50 case target.
"""
from __future__ import annotations

import copy
from datetime import date, timedelta

from app.tools import calculators


def _recent(months: int) -> str:
    return (date.today() - timedelta(days=int(months * 30.44))).isoformat()


def build_base() -> dict:
    price = 400_000.0
    rent = 2_400.0
    taxes = 4_400.0
    insurance = 2_000.0
    payment = calculators.calculate_payment_model(price, 0.20, 0.07, 30, taxes, insurance)
    payment["rate_source_id"] = "assumption:rate"
    investment = calculators.calculate_investment_model(
        price, 0.20, 0.07, 30, rent, 0.05, taxes, insurance, 0.01, 0.08, 0.05
    )
    investment["source_ids"] = ["rentcast:avm-rent", "assumption:rate"]

    comps = [
        {
            "address": "12 Oak St", "distance_miles": 0.4, "sale_price": 395_000.0,
            "sale_date": _recent(3), "bedrooms": 3, "bathrooms": 2,
            "square_footage": 1_750, "price_per_sqft": 225.71,
        },
        {
            "address": "89 Elm Ave", "distance_miles": 0.9, "sale_price": 410_000.0,
            "sale_date": _recent(7), "bedrooms": 3, "bathrooms": 2.5,
            "square_footage": 1_900, "price_per_sqft": 215.79,
        },
    ]

    grounding = {
        "intent": "buyer",
        "purchase_price": price,
        "avm_value": 405_000.0,
        "avm_value_range": [385_000.0, 425_000.0],
        "property_facts": {
            "address": "34 Birch Ln, Springfield, IL 62704",
            "square_footage": 1_800,
            "year_built": 1998,
            "annual_taxes": taxes,
        },
        "payment_model": payment,
        "investment_model": investment,
        "comp_analysis": {
            "comps": comps,
            "subject_price_per_sqft": 222.22,
            "median_comp_price_per_sqft": 220.75,
            "pricing_delta_pct": 0.7,
        },
        "neighborhood_data": {"median_household_income": 68_500.0, "population": 4_210},
        "sources": [],
    }

    report = {
        "report_id": "case-base",
        "generated_at": "2026-07-07T00:00:00+00:00",
        "executive_verdict": {
            "verdict": "Cautious Buy",
            "confidence": "medium",
            "summary": (
                "At $400,000 the subject sits 0.7% above the comp median on a price-per-sqft "
                "basis [rentcast:avm-value], and the all-in monthly payment is "
                f"${payment['all_in_monthly']} [tool:calculate_monthly_payment]."
            ),
            "best_fit_buyer": "A primary-residence buyer planning a 5+ year hold.",
            "worst_fit_buyer": "A cash-flow-focused investor requiring day-one positive cash flow.",
        },
        "property_facts": grounding["property_facts"],
        "payment_model": payment,
        "investment_model": investment,
        "comp_analysis": {
            **grounding["comp_analysis"],
            "narrative": (
                "Both comparables sold within the last year within one mile; the median comp "
                "price per square foot of $220.75 puts the subject essentially at market "
                "[rentcast:avm-value]."
            ),
        },
        "neighborhood": {
            "median_household_income": 68_500.0,
            "population": 4_210,
            "narrative": (
                "The surrounding census tract reports a median household income of $68,500 "
                "across a population of 4,210 [census:acs5]."
            ),
            "source_ids": ["census:acs5"],
        },
        "risk_flags": [
            {"category": "flood", "severity": "low", "detail": "FEMA zone X: outside the high-risk flood area.", "source_ids": ["fema:flood"]}
        ],
        "questions_to_ask": ["What is the age of the roof and HVAC?"],
        "sources": [
            {"id": "rentcast:property", "label": "RentCast property record"},
            {"id": "rentcast:avm-value", "label": "RentCast AVM value & comps"},
            {"id": "rentcast:avm-rent", "label": "RentCast AVM rent estimate"},
            {"id": "census:acs5", "label": "US Census ACS 5-year tract profile"},
            {"id": "fema:flood", "label": "FEMA National Flood Hazard Layer"},
        ],
        "tool_calls": [
            {
                "tool": "calculate_monthly_payment",
                "arguments": {"principal": payment["loan_amount"], "annual_rate": 0.07, "term_years": 30},
                "result": {"result": payment["monthly_principal_interest"]},
            }
        ],
    }
    return {"report": report, "grounding": grounding}


def all_cases() -> list[dict]:
    cases = []

    base = build_base()
    cases.append({"name": "clean_report_passes", "expect_pass": True, **base})

    wrong_math = copy.deepcopy(base)
    wrong_math["report"]["investment_model"]["cap_rate"] = 0.095
    cases.append(
        {"name": "wrong_cap_rate_fails", "expect_pass": False,
         "expect_failure_contains": "cap_rate", **wrong_math}
    )

    hallucinated = copy.deepcopy(base)
    hallucinated["report"]["executive_verdict"]["summary"] += (
        " Nearby homes have gained $85,000 in value over two years [rentcast:avm-value]."
    )
    cases.append(
        {"name": "hallucinated_number_fails", "expect_pass": False,
         "expect_failure_contains": "tool-discipline", **hallucinated}
    )

    no_citation = copy.deepcopy(base)
    no_citation["report"]["neighborhood"]["narrative"] = (
        "This tract shows steady income levels and a stable population."
    )
    cases.append(
        {"name": "missing_citation_fails", "expect_pass": False,
         "expect_failure_contains": "citations", **no_citation}
    )

    steering = copy.deepcopy(base)
    steering["report"]["neighborhood"]["narrative"] += (
        " It is a safe neighborhood that is good for families [census:acs5]."
    )
    cases.append(
        {"name": "fair_housing_language_fails", "expect_pass": False,
         "expect_failure_contains": "fair-housing", **steering}
    )

    guarantee = copy.deepcopy(base)
    guarantee["report"]["executive_verdict"]["summary"] += (
        " This property is guaranteed to appreciate."
    )
    cases.append(
        {"name": "guaranteed_appreciation_fails", "expect_pass": False,
         "expect_failure_contains": "overconfidence", **guarantee}
    )

    far_comp = copy.deepcopy(base)
    far_comp["report"]["comp_analysis"]["comps"].append(
        {"address": "1 Distant Rd", "distance_miles": 6.2, "sale_price": 300_000.0,
         "sale_date": _recent(2), "square_footage": 1_780, "price_per_sqft": 168.54}
    )
    cases.append(
        {"name": "distant_comp_fails", "expect_pass": False,
         "expect_failure_contains": "comps", **far_comp}
    )

    overconfident_avm = copy.deepcopy(base)
    overconfident_avm["grounding"]["avm_value_range"] = [300_000.0, 500_000.0]
    overconfident_avm["report"]["executive_verdict"]["confidence"] = "high"
    cases.append(
        {"name": "high_confidence_wide_avm_fails", "expect_pass": False,
         "expect_failure_contains": "overconfidence", **overconfident_avm}
    )

    fake_source = copy.deepcopy(base)
    fake_source["report"]["comp_analysis"]["narrative"] = (
        "Comparable sales support the list price [mls:listing-feed]."
    )
    cases.append(
        {"name": "unknown_source_id_fails", "expect_pass": False,
         "expect_failure_contains": "unknown source", **fake_source}
    )

    return cases
