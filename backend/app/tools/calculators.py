"""Deterministic underwriting math. The LLM never computes these itself —
it calls these tools and narrates the results. Every function is pure so the
eval harness can recompute and verify any number that appears in a report.
"""
from __future__ import annotations


def calculate_monthly_payment(principal: float, annual_rate: float, term_years: int) -> float:
    """Standard amortized principal + interest payment."""
    if principal <= 0:
        return 0.0
    n = term_years * 12
    if annual_rate <= 0:
        return round(principal / n, 2)
    r = annual_rate / 12
    payment = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return round(payment, 2)


def calculate_payment_model(
    purchase_price: float,
    down_payment_pct: float,
    annual_rate: float,
    term_years: int,
    annual_taxes: float,
    annual_insurance: float,
) -> dict:
    down_payment = round(purchase_price * down_payment_pct, 2)
    loan_amount = round(purchase_price - down_payment, 2)
    monthly_pi = calculate_monthly_payment(loan_amount, annual_rate, term_years)
    monthly_taxes = round(annual_taxes / 12, 2)
    monthly_insurance = round(annual_insurance / 12, 2)
    return {
        "purchase_price": purchase_price,
        "down_payment": down_payment,
        "down_payment_pct": down_payment_pct,
        "loan_amount": loan_amount,
        "annual_rate": annual_rate,
        "term_years": term_years,
        "monthly_principal_interest": monthly_pi,
        "monthly_taxes": monthly_taxes,
        "monthly_insurance": monthly_insurance,
        "all_in_monthly": round(monthly_pi + monthly_taxes + monthly_insurance, 2),
    }


def calculate_noi(
    monthly_rent: float,
    vacancy_rate: float,
    annual_taxes: float,
    annual_insurance: float,
    maintenance_rate: float,
    management_fee_rate: float,
    capex_reserve_rate: float,
) -> dict:
    """NOI excludes debt service. Percentage expense rates apply to gross rent."""
    gross_annual = monthly_rent * 12
    effective_income = gross_annual * (1 - vacancy_rate)
    pct_expenses = gross_annual * (maintenance_rate + management_fee_rate + capex_reserve_rate)
    operating_expenses = round(pct_expenses + annual_taxes + annual_insurance, 2)
    noi = round(effective_income - operating_expenses, 2)
    return {
        "gross_annual_income": round(gross_annual, 2),
        "effective_annual_income": round(effective_income, 2),
        "operating_expenses_annual": operating_expenses,
        "noi_annual": noi,
    }


def calculate_cap_rate(noi_annual: float, purchase_price: float) -> float:
    if purchase_price <= 0:
        return 0.0
    return round(noi_annual / purchase_price, 4)


def calculate_cash_flow(noi_annual: float, monthly_debt_service: float) -> float:
    """Monthly cash flow after debt service."""
    return round(noi_annual / 12 - monthly_debt_service, 2)


def calculate_cash_on_cash(annual_cash_flow: float, cash_invested: float) -> float:
    if cash_invested <= 0:
        return 0.0
    return round(annual_cash_flow / cash_invested, 4)


def calculate_investment_model(
    purchase_price: float,
    down_payment_pct: float,
    annual_rate: float,
    term_years: int,
    monthly_rent: float,
    vacancy_rate: float,
    annual_taxes: float,
    annual_insurance: float,
    maintenance_rate: float,
    management_fee_rate: float,
    capex_reserve_rate: float,
    closing_cost_rate: float = 0.03,
) -> dict:
    payment = calculate_payment_model(
        purchase_price, down_payment_pct, annual_rate, term_years, annual_taxes, annual_insurance
    )
    noi = calculate_noi(
        monthly_rent,
        vacancy_rate,
        annual_taxes,
        annual_insurance,
        maintenance_rate,
        management_fee_rate,
        capex_reserve_rate,
    )
    monthly_cash_flow = calculate_cash_flow(noi["noi_annual"], payment["monthly_principal_interest"])
    cash_invested = round(payment["down_payment"] + purchase_price * closing_cost_rate, 2)
    return {
        **noi,
        "monthly_rent_estimate": monthly_rent,
        "vacancy_rate": vacancy_rate,
        "cap_rate": calculate_cap_rate(noi["noi_annual"], purchase_price),
        "monthly_cash_flow": monthly_cash_flow,
        "cash_invested": cash_invested,
        "cash_on_cash_return": calculate_cash_on_cash(monthly_cash_flow * 12, cash_invested),
    }


def price_per_sqft(price: float | None, sqft: float | None) -> float | None:
    if not price or not sqft:
        return None
    return round(price / sqft, 2)
