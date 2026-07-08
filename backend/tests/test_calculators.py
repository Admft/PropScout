from app.tools import calculators as calc


def test_monthly_payment_standard_loan():
    # $320k at 7% over 30 years — canonical value 2128.97
    assert calc.calculate_monthly_payment(320_000, 0.07, 30) == 2128.97


def test_monthly_payment_zero_rate():
    assert calc.calculate_monthly_payment(120_000, 0.0, 10) == 1000.00


def test_monthly_payment_zero_principal():
    assert calc.calculate_monthly_payment(0, 0.07, 30) == 0.0


def test_payment_model_composition():
    pm = calc.calculate_payment_model(400_000, 0.20, 0.07, 30, 4_400, 2_000)
    assert pm["down_payment"] == 80_000
    assert pm["loan_amount"] == 320_000
    assert pm["monthly_taxes"] == 366.67
    assert pm["monthly_insurance"] == 166.67
    assert pm["all_in_monthly"] == round(
        pm["monthly_principal_interest"] + pm["monthly_taxes"] + pm["monthly_insurance"], 2
    )


def test_noi_excludes_debt_service():
    noi = calc.calculate_noi(2_400, 0.05, 4_400, 2_000, 0.01, 0.08, 0.05)
    assert noi["gross_annual_income"] == 28_800
    assert noi["effective_annual_income"] == 27_360
    # pct expenses: 28800 * 0.14 = 4032; total opex 4032 + 4400 + 2000 = 10432
    assert noi["operating_expenses_annual"] == 10_432
    assert noi["noi_annual"] == 16_928


def test_cap_rate():
    assert calc.calculate_cap_rate(16_928, 400_000) == 0.0423
    assert calc.calculate_cap_rate(10_000, 0) == 0.0


def test_cash_flow_and_coc():
    cf = calc.calculate_cash_flow(16_928, 2_129.21)
    assert cf == round(16_928 / 12 - 2_129.21, 2)
    assert calc.calculate_cash_on_cash(cf * 12, 92_000) == round(cf * 12 / 92_000, 4)
    assert calc.calculate_cash_on_cash(5_000, 0) == 0.0


def test_investment_model_composition():
    im = calc.calculate_investment_model(
        400_000, 0.20, 0.07, 30, 2_400, 0.05, 4_400, 2_000, 0.01, 0.08, 0.05
    )
    assert im["cap_rate"] == calc.calculate_cap_rate(im["noi_annual"], 400_000)
    assert im["cash_invested"] == 80_000 + 12_000  # down payment + 3% closing
    assert im["cash_on_cash_return"] == calc.calculate_cash_on_cash(
        im["monthly_cash_flow"] * 12, im["cash_invested"]
    )


def test_price_per_sqft():
    assert calc.price_per_sqft(400_000, 1_800) == 222.22
    assert calc.price_per_sqft(None, 1_800) is None
    assert calc.price_per_sqft(400_000, None) is None
