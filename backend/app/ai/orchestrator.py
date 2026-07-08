"""Report pipeline: fetch data → compute models deterministically → LLM
narrates with tool-calling → eval harness gates the result.

The LLM only writes narrative and picks the verdict; every number it uses
comes from grounding data or a recorded tool call.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.ai import llm, prompts
from app.config import get_settings
from app.clients import census, fema, fred, rentcast
from app.schemas.report import AnalyzeRequest
from app.tools import calculators, comps, risk
from app.tools.registry import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

MAX_TOOL_TURNS = 8


def gather_grounding(req: AnalyzeRequest) -> dict:
    """Deterministic stage: fetch provider data and compute all core models."""
    settings = get_settings()
    now = datetime.now(timezone.utc).isoformat()
    sources: list[dict] = []

    def add_source(sid: str, label: str) -> None:
        if not any(s["id"] == sid for s in sources):
            sources.append({"id": sid, "label": label, "retrieved_at": now})

    prop = rentcast.get_property(req.address)
    value_est = rentcast.get_value_estimate(req.address)
    rent_est = rentcast.get_rent_estimate(req.address)
    if prop:
        add_source("rentcast:property", "RentCast property record")
    if value_est:
        add_source("rentcast:avm-value", "RentCast AVM value estimate & comparables")
    if rent_est:
        add_source("rentcast:avm-rent", "RentCast AVM long-term rent estimate")

    lat = (prop or {}).get("latitude") or (value_est or {}).get("latitude")
    lon = (prop or {}).get("longitude") or (value_est or {}).get("longitude")

    tract = census.get_tract_profile(lat, lon) if lat and lon else None
    if tract:
        add_source("census:acs5", f"US Census ACS 5-year ({tract['acs_year']}) tract profile")
    flood = fema.get_flood_zone(lat, lon) if lat and lon else None
    if flood:
        add_source("fema:flood", "FEMA National Flood Hazard Layer")

    rate_info = fred.get_mortgage_rate()
    if rate_info:
        annual_rate = rate_info["rate"]
        add_source("fred:mortgage30us", f"FRED 30-yr fixed rate as of {rate_info['as_of']}")
        rate_source = "fred:mortgage30us"
    else:
        annual_rate = settings.default_mortgage_rate
        add_source("assumption:rate", f"Assumed 30-yr rate of {annual_rate:.2%}")
        rate_source = "assumption:rate"

    taxes = _latest_annual_taxes(prop)
    purchase_price = req.purchase_price or (value_est or {}).get("price")
    down_pct = req.down_payment_pct or settings.default_down_payment_pct
    sqft = (prop or {}).get("squareFootage")
    annual_insurance = round((purchase_price or 0) * settings.default_insurance_rate, 2)

    facts = {
        "address": req.address,
        "latitude": lat,
        "longitude": lon,
        "property_type": (prop or {}).get("propertyType"),
        "bedrooms": (prop or {}).get("bedrooms"),
        "bathrooms": (prop or {}).get("bathrooms"),
        "square_footage": sqft,
        "lot_size": (prop or {}).get("lotSize"),
        "year_built": (prop or {}).get("yearBuilt"),
        "last_sale_date": ((prop or {}).get("lastSaleDate") or "")[:10] or None,
        "last_sale_price": (prop or {}).get("lastSalePrice"),
        "annual_taxes": taxes,
        "source_ids": ["rentcast:property"] if prop else [],
    }

    payment_model = None
    investment_model = None
    if purchase_price:
        payment_model = calculators.calculate_payment_model(
            purchase_price, down_pct, annual_rate, settings.default_loan_term_years,
            taxes or 0, annual_insurance,
        )
        payment_model["rate_source_id"] = rate_source
        monthly_rent = (rent_est or {}).get("rent")
        if monthly_rent:
            investment_model = calculators.calculate_investment_model(
                purchase_price, down_pct, annual_rate, settings.default_loan_term_years,
                monthly_rent, settings.default_vacancy_rate, taxes or 0, annual_insurance,
                settings.default_maintenance_rate, settings.default_management_fee_rate,
                settings.default_capex_reserve_rate,
            )
            investment_model["rent_range_low"] = (rent_est or {}).get("rentRangeLow")
            investment_model["rent_range_high"] = (rent_est or {}).get("rentRangeHigh")
            investment_model["source_ids"] = ["rentcast:avm-rent", rate_source]

    raw_comps = (value_est or {}).get("comparables") or []
    selected = comps.select_comps(raw_comps, sqft, facts["property_type"])
    comp_analysis = comps.analyze_pricing(selected, purchase_price, sqft)
    comp_analysis["source_ids"] = ["rentcast:avm-value"] if value_est else []

    risk_flags = risk.build_risk_flags(flood, facts["year_built"], taxes, purchase_price)

    return {
        "generated_at": now,
        "intent": req.intent,
        "purchase_price": purchase_price,
        "avm_value": (value_est or {}).get("price"),
        "avm_value_range": [
            (value_est or {}).get("priceRangeLow"),
            (value_est or {}).get("priceRangeHigh"),
        ],
        "property_facts": facts,
        "payment_model": payment_model,
        "investment_model": investment_model,
        "comp_analysis": comp_analysis,
        "neighborhood_data": tract,
        "risk_flags": risk_flags,
        "sources": sources,
    }


def _latest_annual_taxes(prop: Optional[dict]) -> Optional[float]:
    taxes = (prop or {}).get("propertyTaxes")
    if not taxes:
        return None
    latest_year = max(taxes.keys())
    return (taxes[latest_year] or {}).get("total")


def run_tool_loop(system: str, user_content: str, extra_tools: list[dict]) -> tuple[dict | None, list[dict], str]:
    """Run the LLM tool-calling loop. Returns (submitted_args, tool_call_records, final_text).

    `submitted_args` is the input of the final submit_* call if the model made one.
    """
    tools = TOOL_DEFINITIONS + extra_tools
    submit_names = {t["name"] for t in extra_tools}
    messages: list[dict] = [{"role": "user", "content": user_content}]
    records: list[dict] = []

    for _ in range(MAX_TOOL_TURNS):
        resp = llm.chat(system, messages, tools)
        if not resp.tool_calls:
            if submit_names:
                messages.append({"role": "assistant", "content": resp.text or "(empty)"})
                messages.append(
                    {"role": "user", "content": "You must finish by calling the submit tool with all required sections."}
                )
                continue
            return None, records, resp.text

        messages.append(
            {
                "role": "assistant",
                "content": resp.text,
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in resp.tool_calls
                ],
            }
        )
        for tc in resp.tool_calls:
            if tc.name in submit_names:
                return tc.arguments, records, resp.text
            result = execute_tool(tc.name, tc.arguments)
            records.append({"tool": tc.name, "arguments": tc.arguments, "result": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": json.dumps(result),
                }
            )

    raise RuntimeError("LLM did not submit a report within the tool-call budget")


def generate_report(req: AnalyzeRequest) -> dict:
    grounding = gather_grounding(req)

    user_content = (
        f"Buyer intent: {req.intent}\n\nGROUNDING DATA (the only permitted source of facts):\n"
        + json.dumps(grounding, indent=2, default=str)
    )
    narrative, tool_records, _ = run_tool_loop(
        prompts.REPORT_SYSTEM, user_content, [prompts.SUBMIT_REPORT_TOOL]
    )
    if narrative is None:
        raise RuntimeError("Report narrative was not produced")

    report = {
        "report_id": uuid.uuid4().hex[:12],
        "generated_at": grounding["generated_at"],
        "intent": req.intent,
        "disclaimer": "HouseFax is a decision-support tool, not financial, legal, or real-estate advice.",
        "executive_verdict": {
            "verdict": narrative["verdict"],
            "confidence": narrative["confidence"],
            "summary": narrative["verdict_summary"],
            "best_fit_buyer": narrative["best_fit_buyer"],
            "worst_fit_buyer": narrative["worst_fit_buyer"],
        },
        "property_facts": grounding["property_facts"],
        "payment_model": grounding["payment_model"],
        "investment_model": grounding["investment_model"],
        "comp_analysis": {**grounding["comp_analysis"], "narrative": narrative["comp_narrative"]},
        "neighborhood": {
            "median_household_income": (grounding["neighborhood_data"] or {}).get(
                "median_household_income"
            ),
            "population": (grounding["neighborhood_data"] or {}).get("population"),
            "narrative": narrative["neighborhood_narrative"],
            "source_ids": ["census:acs5"] if grounding["neighborhood_data"] else [],
        },
        "risk_flags": grounding["risk_flags"],
        "questions_to_ask": narrative["questions_to_ask"],
        "sources": grounding["sources"],
        "tool_calls": tool_records,
    }

    from evals.runner import run_evals  # imported here to avoid a circular import

    eval_result = run_evals(report, grounding)
    report["eval_passed"] = eval_result["passed"]
    report["eval_failures"] = eval_result["failures"]
    return report


def answer_question(report: dict, question: str) -> dict:
    user_content = (
        "REPORT JSON:\n" + json.dumps(report, indent=2, default=str) + f"\n\nQUESTION: {question}"
    )
    _, records, text = run_tool_loop(prompts.QA_SYSTEM, user_content, [])
    cited = sorted({s["id"] for s in report.get("sources", []) if f"[{s['id']}]" in text})
    return {"answer": text, "source_ids": cited, "tool_calls": records}
