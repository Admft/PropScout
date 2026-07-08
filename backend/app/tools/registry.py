"""Tool definitions exposed to the LLM, plus the dispatcher that executes
them. Every execution is recorded so the eval harness can verify that any
number in the narrative traces back to a tool result or grounding data.
"""
from __future__ import annotations

import inspect

from app.tools import calculators

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "calculate_monthly_payment",
        "description": "Amortized monthly principal+interest payment for a loan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "principal": {"type": "number"},
                "annual_rate": {"type": "number", "description": "e.g. 0.07 for 7%"},
                "term_years": {"type": "integer"},
            },
            "required": ["principal", "annual_rate", "term_years"],
        },
    },
    {
        "name": "calculate_cap_rate",
        "description": "Cap rate = annual NOI / purchase price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "noi_annual": {"type": "number"},
                "purchase_price": {"type": "number"},
            },
            "required": ["noi_annual", "purchase_price"],
        },
    },
    {
        "name": "calculate_cash_flow",
        "description": "Monthly cash flow = NOI/12 minus monthly debt service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "noi_annual": {"type": "number"},
                "monthly_debt_service": {"type": "number"},
            },
            "required": ["noi_annual", "monthly_debt_service"],
        },
    },
    {
        "name": "calculate_cash_on_cash",
        "description": "Cash-on-cash return = annual cash flow / total cash invested.",
        "input_schema": {
            "type": "object",
            "properties": {
                "annual_cash_flow": {"type": "number"},
                "cash_invested": {"type": "number"},
            },
            "required": ["annual_cash_flow", "cash_invested"],
        },
    },
]

_IMPLEMENTATIONS = {
    "calculate_monthly_payment": calculators.calculate_monthly_payment,
    "calculate_cap_rate": calculators.calculate_cap_rate,
    "calculate_cash_flow": calculators.calculate_cash_flow,
    "calculate_cash_on_cash": calculators.calculate_cash_on_cash,
}


def execute_tool(name: str, arguments: dict) -> dict:
    fn = _IMPLEMENTATIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    sig = inspect.signature(fn)
    try:
        kwargs = {k: arguments[k] for k in sig.parameters if k in arguments}
        return {"result": fn(**kwargs)}
    except (TypeError, KeyError, ValueError) as exc:
        return {"error": str(exc)}
