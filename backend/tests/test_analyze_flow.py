"""End-to-end /analyze flow with mocked providers and a scripted LLM.

Exercises the real orchestrator, tool-calling loop, report assembly, eval
gate, and FastAPI serialization — everything except the network.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.ai.llm import LLMResponse, ToolCall
from app.main import app


def _iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT00:00:00.000Z"
    )


FAKE_PROPERTY = {
    "formattedAddress": "34 Birch Ln, Springfield, IL 62704",
    "latitude": 39.78,
    "longitude": -89.65,
    "propertyType": "Single Family",
    "bedrooms": 3,
    "bathrooms": 2,
    "squareFootage": 1800,
    "lotSize": 8000,
    "yearBuilt": 1998,
    "lastSaleDate": "2019-06-20T00:00:00.000Z",
    "lastSalePrice": 310000,
    "propertyTaxes": {"2025": {"total": 4400}},
}

FAKE_VALUE = {
    "price": 405000,
    "priceRangeLow": 385000,
    "priceRangeHigh": 425000,
    "comparables": [
        {
            "formattedAddress": "12 Oak St",
            "distance": 0.4,
            "price": 395000,
            "removedDate": _iso_days_ago(90),
            "bedrooms": 3,
            "bathrooms": 2,
            "squareFootage": 1750,
            "propertyType": "Single Family",
        },
        {
            "formattedAddress": "89 Elm Ave",
            "distance": 0.9,
            "price": 410000,
            "removedDate": _iso_days_ago(200),
            "bedrooms": 3,
            "bathrooms": 2.5,
            "squareFootage": 1900,
            "propertyType": "Single Family",
        },
    ],
}

FAKE_RENT = {"rent": 2400, "rentRangeLow": 2200, "rentRangeHigh": 2600}
FAKE_TRACT = {"median_household_income": 68500.0, "population": 4210, "acs_year": 2023}
FAKE_FLOOD = {"zone": "X", "subtype": None, "high_risk": False}


def scripted_llm():
    """First call: use a calculator tool. Second call: submit the narrative."""
    calls = {"n": 0}

    def chat(system: str, messages: list[dict], tools: list[dict]) -> LLMResponse:
        calls["n"] += 1
        if calls["n"] == 1:
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="t1",
                        name="calculate_monthly_payment",
                        arguments={"principal": 320000, "annual_rate": 0.07, "term_years": 30},
                    )
                ]
            )
        return LLMResponse(
            tool_calls=[
                ToolCall(
                    id="t2",
                    name="submit_report_narrative",
                    arguments={
                        "verdict": "Cautious Buy",
                        "confidence": "medium",
                        "verdict_summary": (
                            "The subject is priced near its comparable sales on a per-square-foot "
                            "basis [rentcast:avm-value], and the payment model reflects the "
                            "computed principal and interest [tool:calculate_monthly_payment]."
                        ),
                        "best_fit_buyer": "A primary-residence buyer planning a long hold.",
                        "worst_fit_buyer": "An investor who needs day-one positive cash flow.",
                        "comp_narrative": (
                            "Both comparables sold recently within a mile of the subject and "
                            "bracket its size [rentcast:avm-value]."
                        ),
                        "neighborhood_narrative": (
                            "The surrounding census tract reports a median household income of "
                            "$68,500 across a population of 4,210 [census:acs5]."
                        ),
                        "questions_to_ask": [
                            "What is the age of the roof and HVAC?",
                            "Has the seller disclosed any water intrusion?",
                        ],
                    },
                )
            ]
        )

    return chat


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.clients.rentcast.get_property", lambda address: FAKE_PROPERTY)
    monkeypatch.setattr("app.clients.rentcast.get_value_estimate", lambda address: FAKE_VALUE)
    monkeypatch.setattr("app.clients.rentcast.get_rent_estimate", lambda address: FAKE_RENT)
    monkeypatch.setattr("app.clients.census.get_tract_profile", lambda lat, lon: FAKE_TRACT)
    monkeypatch.setattr("app.clients.fema.get_flood_zone", lambda lat, lon: FAKE_FLOOD)
    monkeypatch.setattr("app.clients.fred.get_mortgage_rate", lambda: None)
    monkeypatch.setattr("app.ai.llm.chat", scripted_llm())
    return TestClient(app)


def test_analyze_end_to_end(client):
    resp = client.post(
        "/analyze",
        json={
            "address": "34 Birch Ln, Springfield, IL 62704",
            "purchase_price": 400000,
            "down_payment_pct": 0.20,
            "intent": "buyer",
        },
    )
    assert resp.status_code == 200, resp.text
    report = resp.json()

    # deterministic models came from the calculators, not the LLM
    assert report["payment_model"]["loan_amount"] == 320000
    assert report["payment_model"]["monthly_principal_interest"] == 2128.97
    assert report["investment_model"]["monthly_rent_estimate"] == 2400
    assert report["executive_verdict"]["verdict"] == "Cautious Buy"

    # the LLM's calculator call was recorded for auditability
    assert any(tc["tool"] == "calculate_monthly_payment" for tc in report["tool_calls"])

    # both comps survived quality filtering
    assert len(report["comp_analysis"]["comps"]) == 2

    # the eval gate ran and the report shipped clean
    assert report["eval_failures"] == []
    assert report["eval_passed"] is True

    # follow-up retrieval works through the cache
    fetched = client.get(f"/reports/{report['report_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["report_id"] == report["report_id"]


def test_analyze_returns_404_when_address_resolves_nothing(client, monkeypatch):
    monkeypatch.setattr("app.clients.rentcast.get_property", lambda address: None)
    monkeypatch.setattr("app.clients.rentcast.get_value_estimate", lambda address: None)
    monkeypatch.setattr("app.clients.rentcast.get_rent_estimate", lambda address: None)
    resp = client.post("/analyze", json={"address": "nowhere at all", "intent": "buyer"})
    assert resp.status_code == 404
