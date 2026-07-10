"""The report contract shared with the frontend.

Numeric fields are produced by deterministic tools; narrative fields are
produced by the LLM and must cite the sources listed in `sources`.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    strong_candidate = "Strong Candidate"
    cautious_buy = "Cautious Buy"
    pass_ = "Pass"


class Source(BaseModel):
    id: str  # e.g. "rentcast:property", "fema:flood", "tool:calculate_monthly_payment"
    label: str
    retrieved_at: Optional[str] = None


class PropertyFacts(BaseModel):
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = None
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    last_sale_date: Optional[str] = None
    last_sale_price: Optional[float] = None
    annual_taxes: Optional[float] = None
    source_ids: list[str] = Field(default_factory=list)


class PaymentModel(BaseModel):
    purchase_price: float
    down_payment: float
    down_payment_pct: float
    loan_amount: float
    annual_rate: float
    rate_source_id: str = "assumption:rate"
    term_years: int
    monthly_principal_interest: float
    monthly_taxes: float
    monthly_insurance: float
    all_in_monthly: float


class InvestmentModel(BaseModel):
    monthly_rent_estimate: float
    rent_range_low: Optional[float] = None
    rent_range_high: Optional[float] = None
    vacancy_rate: float
    gross_annual_income: float
    operating_expenses_annual: float
    noi_annual: float
    cap_rate: float
    monthly_cash_flow: float
    cash_invested: float
    cash_on_cash_return: float
    source_ids: list[str] = Field(default_factory=list)


class Comp(BaseModel):
    address: str
    distance_miles: Optional[float] = None
    sale_price: Optional[float] = None
    sale_date: Optional[str] = None
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[int] = None
    price_per_sqft: Optional[float] = None
    similarity_note: Optional[str] = None


class CompAnalysis(BaseModel):
    comps: list[Comp]
    subject_price_per_sqft: Optional[float] = None
    median_comp_price_per_sqft: Optional[float] = None
    pricing_delta_pct: Optional[float] = None  # +5 = subject priced 5% above comp median
    narrative: str = ""
    source_ids: list[str] = Field(default_factory=list)


class RiskFlag(BaseModel):
    category: str  # flood | wildfire | insurance | taxes | maintenance
    severity: str  # low | moderate | high | unknown
    detail: str
    source_ids: list[str] = Field(default_factory=list)


class NeighborhoodThesis(BaseModel):
    median_household_income: Optional[float] = None
    population: Optional[int] = None
    narrative: str = ""
    source_ids: list[str] = Field(default_factory=list)


class ExecutiveVerdict(BaseModel):
    verdict: Verdict
    confidence: str  # low | medium | high
    summary: str
    best_fit_buyer: str
    worst_fit_buyer: str


class ToolCallRecord(BaseModel):
    tool: str
    arguments: dict
    result: dict


class Report(BaseModel):
    report_id: str
    generated_at: str
    intent: str = "buyer"
    disclaimer: str = (
        "HouseFax is a decision-support tool, not financial, legal, or real-estate advice."
    )
    executive_verdict: ExecutiveVerdict
    property_facts: PropertyFacts
    payment_model: Optional[PaymentModel] = None
    investment_model: Optional[InvestmentModel] = None
    comp_analysis: CompAnalysis
    neighborhood: NeighborhoodThesis
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    eval_passed: Optional[bool] = None
    eval_failures: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    address: str
    purchase_price: Optional[float] = None
    down_payment_pct: Optional[float] = None
    intent: str = "buyer"  # buyer | investor


class QARequest(BaseModel):
    report_id: str
    question: str


class QAResponse(BaseModel):
    answer: str
    source_ids: list[str] = Field(default_factory=list)
