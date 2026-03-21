import azure.functions as func
import logging
import json
import os
import requests
import re
import datetime
import statistics
from apify_client import ApifyClient
from openai import OpenAI
from azure.cosmos import CosmosClient, PartitionKey

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ---------------------------------------------------------
# CONFIGURATION & CLIENTS
# ---------------------------------------------------------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
RENTCAST_KEY = os.getenv("RENTCAST_API_KEY")
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")

openai_client = None
container = None

try:
    if OPENAI_KEY:
        openai_client = OpenAI(api_key=OPENAI_KEY)

    db_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = db_client.create_database_if_not_exists(id="propscout-db")
    container = database.create_container_if_not_exists(id="reports", partition_key=PartitionKey(path="/id"))
    print("✅ Successfully connected to Cosmos DB!")
except Exception as e:
    print(f"❌ CRITICAL ERROR ON STARTUP: {e}")
    container = None


# ---------------------------------------------------------
# CORE HELPERS
# ---------------------------------------------------------
def clamp(value, low, high):
    return max(low, min(high, value))


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def unique_nonempty(items):
    seen = set()
    out = []
    for item in items:
        if not item:
            continue
        norm = str(item).strip()
        if not norm:
            continue
        key = norm.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(norm)
    return out


def parse_rent_amount(value):
    """Parse a plausible monthly rent from mixed numeric/string values."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        amount = float(value)
    elif isinstance(value, str):
        cleaned = re.sub(r"[^\d.]", "", value)
        if not cleaned:
            return None
        amount = safe_float(cleaned, default=0.0)
    else:
        return None

    # Guardrail: reject implausible monthly rents.
    if amount <= 0 or amount < 300 or amount > 50000:
        return None
    return amount


def extract_rent_from_listing_history(listing_data):
    """
    Best-effort rent fallback from Zillow history-like arrays.
    Handles inconsistent scraper schemas and returns the most recent rent-like event.
    """
    if not isinstance(listing_data, dict):
        return None

    history_candidates = []
    for key, value in listing_data.items():
        key_l = str(key).lower()
        if isinstance(value, list) and ("history" in key_l or "price" in key_l or "event" in key_l):
            history_candidates.append(value)

    rent_events = []
    rent_keywords = ("rent", "rental", "leased", "lease")
    rent_value_keys = ("rent", "rentalprice", "monthlyrent", "price", "listprice", "amount")
    date_keys = ("date", "eventdate", "posteddate", "time", "datetime")

    for history in history_candidates:
        if not isinstance(history, list):
            continue

        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                continue

            text_blob = " ".join(
                str(item.get(k, "")).lower()
                for k in ("event", "eventType", "type", "description", "source", "status")
            )
            has_rent_signal = any(keyword in text_blob for keyword in rent_keywords)

            amount = None
            for key in rent_value_keys:
                for candidate_key in (key, key.title(), key.upper()):
                    if candidate_key in item:
                        amount = parse_rent_amount(item.get(candidate_key))
                        if amount:
                            break
                if amount:
                    break

            if not has_rent_signal or not amount:
                continue

            # Use max parsed date digits as a lightweight recency score.
            recency = 0
            for dkey in date_keys:
                if dkey in item and item.get(dkey) is not None:
                    digits = re.sub(r"\D", "", str(item.get(dkey)))
                    if len(digits) >= 8:
                        recency = max(recency, safe_int(digits[:14], 0))

            rent_events.append((recency, idx, amount))

    if not rent_events:
        return None

    rent_events.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return round(rent_events[0][2], 2)


# ---------------------------------------------------------
# HELPER: AUTO-PARSE URL
# ---------------------------------------------------------
def extract_address_from_url(url):
    logging.info("🕵️‍♂️ Attempting to auto-parse address directly from URL...")
    # Matches the pattern in zillow.com/homedetails/123-Main-St-City-TX-75000/
    match = re.search(r'homedetails/([^/]+)/', url)
    if match:
        raw_string = match.group(1)
        clean_address = raw_string.replace('-', ' ')
        logging.info(f"✅ Auto-parsed address: {clean_address}")
        return clean_address
    return None


# ---------------------------------------------------------
# DATA PIPELINE
# ---------------------------------------------------------
def get_rentcast_data(address):
    logging.info(f"📡 Fetching RentCast Valuation for: {address}")
    url = "https://api.rentcast.io/v1/avm/value"
    params = {"address": address, "propertyType": "Single Family"}
    headers = {"accept": "application/json", "X-Api-Key": RENTCAST_KEY}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logging.error(f"RentCast Failed: {e}")
    return {}


def get_neighborhood_comps(address):
    logging.info(f"🏘️ Fetching Neighborhood Comps for: {address}")
    url = "https://api.rentcast.io/v1/sales/comps"
    params = {"address": address, "propertyType": "Single Family", "radius": 2, "limit": 12}
    headers = {"accept": "application/json", "X-Api-Key": RENTCAST_KEY}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        if response.status_code != 200:
            return {
                "average_comp_price": 0,
                "median_comp_price": 0,
                "comp_count": 0,
                "average_comp_price_per_sqft": 0,
                "comps": []
            }

        comps = response.json()
        if not isinstance(comps, list) or len(comps) == 0:
            return {
                "average_comp_price": 0,
                "median_comp_price": 0,
                "comp_count": 0,
                "average_comp_price_per_sqft": 0,
                "comps": []
            }

        clean_comps = []
        prices = []
        price_per_sqft_values = []

        for comp in comps:
            price = safe_float(comp.get('price'))
            sqft = safe_float(comp.get('squareFootage') or comp.get('livingArea'))
            distance = safe_float(comp.get('distance'))
            if price <= 0:
                continue

            prices.append(price)

            ppsf = 0
            if sqft > 0:
                ppsf = price / sqft
                price_per_sqft_values.append(ppsf)

            clean_comps.append({
                "price": round(price, 2),
                "square_footage": round(sqft, 2) if sqft > 0 else 0,
                "distance_miles": round(distance, 2) if distance > 0 else 0,
                "price_per_sqft": round(ppsf, 2) if ppsf > 0 else 0,
                "sold_date": comp.get('soldDate')
            })

        if not prices:
            return {
                "average_comp_price": 0,
                "median_comp_price": 0,
                "comp_count": 0,
                "average_comp_price_per_sqft": 0,
                "comps": []
            }

        avg_comp_price = statistics.mean(prices)
        median_comp_price = statistics.median(prices)
        avg_ppsf = statistics.mean(price_per_sqft_values) if price_per_sqft_values else 0

        return {
            "average_comp_price": round(avg_comp_price, 2),
            "median_comp_price": round(median_comp_price, 2),
            "comp_count": len(prices),
            "average_comp_price_per_sqft": round(avg_ppsf, 2),
            "comps": clean_comps[:8]
        }

    except Exception as e:
        logging.error(f"RentCast Comps Failed: {e}")

    return {
        "average_comp_price": 0,
        "median_comp_price": 0,
        "comp_count": 0,
        "average_comp_price_per_sqft": 0,
        "comps": []
    }


def scrape_zillow(zillow_url):
    logging.info("🕷️ Scraping Zillow for property specs and description...")
    try:
        client = ApifyClient(APIFY_TOKEN)
        run_input = {"startUrls": [{"url": zillow_url}], "maxItems": 1}
        run = client.actor("maxcopell/zillow-detail-scraper").call(run_input=run_input)
        dataset = client.dataset(run["defaultDatasetId"]).list_items().items
        if dataset:
            return dataset[0]
    except Exception as e:
        logging.error(f"Apify Failed: {e}")
    return {}


# ---------------------------------------------------------
# VALUATION ENGINE
# ---------------------------------------------------------
def build_valuation_model(listing_data, financial_data, comps_data, property_specs, monthly_rent):
    listing_price = safe_float(listing_data.get('price'))
    zestimate = safe_float(listing_data.get('zestimate'))
    rentcast_price = safe_float(financial_data.get('price'))
    comp_avg = safe_float(comps_data.get('average_comp_price'))
    comp_median = safe_float(comps_data.get('median_comp_price'))
    comp_ppsf = safe_float(comps_data.get('average_comp_price_per_sqft'))
    sqft = safe_float(property_specs.get('sqft'))
    year_built = safe_int(property_specs.get('yearBuilt'))

    signals = []

    if listing_price > 0:
        signals.append({"name": "zillow_list_price", "value": listing_price, "weight": 0.22})

    if zestimate > 0:
        signals.append({"name": "zillow_zestimate", "value": zestimate, "weight": 0.12})

    if rentcast_price > 0:
        signals.append({"name": "rentcast_avm", "value": rentcast_price, "weight": 0.34})

    if comp_median > 0:
        signals.append({"name": "comps_median", "value": comp_median, "weight": 0.22})

    if comp_avg > 0:
        signals.append({"name": "comps_average", "value": comp_avg, "weight": 0.14})

    if comp_ppsf > 0 and sqft > 0:
        comp_ppsf_value = comp_ppsf * sqft
        signals.append({"name": "comps_price_per_sqft", "value": comp_ppsf_value, "weight": 0.18})

    monthly_rent_value = safe_float(monthly_rent, default=0.0)
    has_rent = monthly_rent_value > 0

    if has_rent:
        annual_gross = monthly_rent_value * 12
        expense_ratio = 0.38
        if year_built and year_built < 1990:
            expense_ratio += 0.03
        elif year_built and year_built > 2018:
            expense_ratio -= 0.02

        implied_noi = annual_gross * (1 - clamp(expense_ratio, 0.30, 0.50))
        target_cap_rate = 0.0625
        rent_based_value = implied_noi / target_cap_rate if target_cap_rate > 0 else 0
        if rent_based_value > 0:
            signals.append({"name": "income_approach", "value": rent_based_value, "weight": 0.20})

    clean_values = [s["value"] for s in signals if s["value"] > 0]
    if not clean_values:
        return {
            "estimated_value": 0,
            "valuation_low": 0,
            "valuation_high": 0,
            "confidence_score": 25,
            "price_vs_value_delta": 0,
            "price_vs_value_delta_pct": 0,
            "valuation_status": "unknown",
            "suggested_offer": 0,
            "signals": []
        }

    center = statistics.median(clean_values)

    for signal in signals:
        val = signal["value"]
        if center > 0 and (val < center * 0.55 or val > center * 1.80):
            signal["outlier"] = True
            signal["adjusted_weight"] = signal["weight"] * 0.2
        else:
            signal["outlier"] = False
            signal["adjusted_weight"] = signal["weight"]

    weight_sum = sum(s["adjusted_weight"] for s in signals if s["value"] > 0)
    if weight_sum == 0:
        estimate = center
    else:
        estimate = sum(s["value"] * s["adjusted_weight"] for s in signals if s["value"] > 0) / weight_sum

    variance = 0.0
    if weight_sum > 0:
        variance = sum(
            s["adjusted_weight"] * ((s["value"] - estimate) ** 2)
            for s in signals if s["value"] > 0
        ) / weight_sum

    std_dev = variance ** 0.5
    dispersion_ratio = (std_dev / estimate) if estimate > 0 else 1.0

    comp_count = safe_int(comps_data.get("comp_count"))
    confidence = 84
    confidence -= min(30, int(dispersion_ratio * 100))
    confidence -= 6 if len(signals) < 4 else 0
    confidence -= 8 if comp_count < 3 else 0
    # Missing rent should reduce confidence, but not imply zero-income distress.
    confidence -= 6 if not has_rent else 0
    confidence -= 5 if rentcast_price <= 0 else 0
    confidence += 4 if len(signals) >= 6 else 0
    confidence = clamp(confidence, 25, 95)

    range_pct = 0.07 + min(0.18, dispersion_ratio * 0.9)
    if confidence < 55:
        range_pct += 0.05

    valuation_low = estimate * (1 - range_pct)
    valuation_high = estimate * (1 + range_pct)

    ask_price = listing_price or rentcast_price or 0
    delta = (ask_price - estimate) if ask_price > 0 else 0
    delta_pct = (delta / estimate) if estimate > 0 and ask_price > 0 else 0

    if ask_price <= 0:
        valuation_status = "unknown"
    elif delta_pct >= 0.12:
        valuation_status = "overpriced"
    elif delta_pct >= 0.05:
        valuation_status = "slightly_overpriced"
    elif delta_pct <= -0.10:
        valuation_status = "undervalued"
    elif delta_pct <= -0.04:
        valuation_status = "slightly_undervalued"
    else:
        valuation_status = "fair_value"

    suggested_offer = 0
    if estimate > 0:
        suggested_offer = estimate * (0.96 if confidence >= 70 else 0.92)

    return {
        "estimated_value": round(estimate, 2),
        "valuation_low": round(valuation_low, 2),
        "valuation_high": round(valuation_high, 2),
        "confidence_score": int(confidence),
        "price_vs_value_delta": round(delta, 2),
        "price_vs_value_delta_pct": round(delta_pct * 100, 2),
        "valuation_status": valuation_status,
        "suggested_offer": round(suggested_offer, 2),
        "signals": [
            {
                "name": s["name"],
                "value": round(s["value"], 2),
                "base_weight": round(s["weight"], 3),
                "adjusted_weight": round(s["adjusted_weight"], 3),
                "outlier": s["outlier"]
            }
            for s in signals
        ]
    }


# ---------------------------------------------------------
# FINANCIAL ENGINE
# ---------------------------------------------------------
def calculate_financials(price, monthly_rent):
    logging.info("🧮 Crunching hard financial metrics...")

    price_value = safe_float(price, default=0.0)
    monthly_rent_value = safe_float(monthly_rent, default=0.0)
    has_price = price_value > 0
    has_rent = monthly_rent_value > 0

    # Business logic: missing rent is unknown input, not zero performance.
    if not has_price or not has_rent:
        if has_price and not has_rent:
            data_quality_flag = "missing_rent"
        elif not has_price and not has_rent:
            data_quality_flag = "missing_price_and_rent"
        else:
            data_quality_flag = "missing_price"

        return {
            "purchase_price": round(price_value, 2) if has_price else None,
            "monthly_rent_est": round(monthly_rent_value, 2) if has_rent else None,
            "annual_gross_rent": None,
            "annual_expenses_est": None,
            "noi": None,
            "cap_rate": None,
            "dscr": None,
            "annual_debt_service": None,
            "annual_cash_flow_after_debt": None,
            "breakeven_occupancy": None,
            "data_quality_flag": data_quality_flag
        }

    annual_gross_rent = monthly_rent_value * 12
    vacancy = annual_gross_rent * 0.05
    effective_gross_income = annual_gross_rent - vacancy

    taxes = price_value * 0.022
    insurance = price_value * 0.005
    maintenance = price_value * 0.010
    capex_reserve = annual_gross_rent * 0.05
    property_mgmt = effective_gross_income * 0.08

    annual_expenses = taxes + insurance + maintenance + capex_reserve + property_mgmt
    noi = effective_gross_income - annual_expenses
    cap_rate = (noi / price_value) * 100 if price_value > 0 else None

    principal = price_value * 0.80
    monthly_rate = 0.07 / 12
    n_payments = 360

    monthly_mortgage = principal * (monthly_rate * (1 + monthly_rate) ** n_payments) / ((1 + monthly_rate) ** n_payments - 1)
    annual_debt_service = monthly_mortgage * 12

    dscr = noi / annual_debt_service if annual_debt_service > 0 else 0
    annual_cash_flow_after_debt = noi - annual_debt_service
    breakeven_occupancy = (annual_expenses + annual_debt_service) / annual_gross_rent if annual_gross_rent > 0 else 0

    return {
        "purchase_price": round(price_value, 2),
        "monthly_rent_est": round(monthly_rent_value, 2),
        "annual_gross_rent": round(annual_gross_rent, 2),
        "annual_expenses_est": round(annual_expenses, 2),
        "noi": round(noi, 2),
        "cap_rate": round(cap_rate, 2),
        "dscr": round(dscr, 2),
        "annual_debt_service": round(annual_debt_service, 2),
        "annual_cash_flow_after_debt": round(annual_cash_flow_after_debt, 2),
        "breakeven_occupancy": round(breakeven_occupancy * 100, 2),
        "data_quality_flag": "ok"
    }


# ---------------------------------------------------------
# RULE-BASED UNDERWRITER
# ---------------------------------------------------------
def run_algorithmic_underwrite(valuation_model, financial_metrics, comps_data, property_specs):
    score = 100
    critical_flags = []
    market_warnings = []
    value_add_opportunities = []

    cap_rate = financial_metrics.get("cap_rate")
    dscr = financial_metrics.get("dscr")
    cash_flow = financial_metrics.get("annual_cash_flow_after_debt")
    breakeven = financial_metrics.get("breakeven_occupancy")
    data_quality_flag = financial_metrics.get("data_quality_flag")
    valuation_conf = safe_int(valuation_model.get("confidence_score"))
    price_delta_pct = safe_float(valuation_model.get("price_vs_value_delta_pct"))
    valuation_status = valuation_model.get("valuation_status", "unknown")
    comp_count = safe_int(comps_data.get("comp_count"))
    year_built = safe_int(property_specs.get("yearBuilt"))

    missing_rent_metrics = data_quality_flag in {"missing_rent", "missing_price_and_rent"} or (
        cap_rate is None or dscr is None or cash_flow is None or breakeven is None
    )

    # Missing rent => incomplete underwriting, not zero operating performance.
    if missing_rent_metrics:
        market_warnings.append("Rent estimate unavailable; cash-flow metrics could not be computed.")
        score -= 8
    else:
        if cap_rate < 5.0:
            critical_flags.append(f"Cap rate is weak at {cap_rate:.2f}% (<5.0%).")
            score -= 22
        elif cap_rate < 6.0:
            market_warnings.append(f"Cap rate is thin at {cap_rate:.2f}%; margin for error is low.")
            score -= 10

        if dscr < 1.10:
            critical_flags.append(f"DSCR is {dscr:.2f}; debt coverage is stressed.")
            score -= 28
        elif dscr < 1.25:
            market_warnings.append(f"DSCR is only {dscr:.2f}; financing cushion is limited.")
            score -= 12

        if cash_flow < 0:
            critical_flags.append("Annual cash flow after debt service is negative.")
            score -= 16

        if breakeven > 92:
            market_warnings.append(f"Break-even occupancy is high at {breakeven:.2f}%.")
            score -= 8

    if valuation_status in {"overpriced", "slightly_overpriced"}:
        if price_delta_pct >= 12:
            critical_flags.append(f"Asking price is about {price_delta_pct:.2f}% above model value.")
            score -= 18
        else:
            market_warnings.append(f"Asking price is {price_delta_pct:.2f}% above model value.")
            score -= 9

    if valuation_status in {"undervalued", "slightly_undervalued"}:
        value_add_opportunities.append("Modeled value is above ask; this may be an immediate pricing edge.")

    if comp_count < 3:
        market_warnings.append("Low comp depth; valuation confidence is constrained.")
        score -= 7

    if year_built and year_built < 1980:
        market_warnings.append("Older build vintage may imply higher deferred maintenance risk.")
        score -= 6

    if valuation_conf < 55:
        market_warnings.append("Valuation confidence is modest; treat numbers as directional.")
        score -= 8

    score = int(clamp(score, 0, 100))

    if valuation_status == "overpriced":
        value_add_opportunities.append("Offer below ask and anchor to comp median plus repair reserve.")
    if cap_rate is not None and cap_rate < 6.0:
        value_add_opportunities.append("Increase NOI via rent optimization and operating expense cuts before refinance.")
    if dscr is not None and dscr < 1.25:
        value_add_opportunities.append("Lower leverage or buy rate down to improve DSCR stability.")

    # Manual review for incomplete underwriting due to missing rent inputs.
    if missing_rent_metrics:
        deal_status = "MANUAL_REVIEW"
    else:
        deal_status = "PASS"
        if score < 68 or len(critical_flags) >= 2:
            deal_status = "REJECT"

    summary = (
        f"Model score is {score}/100 with valuation confidence {valuation_conf}/100. "
        f"Property screens as {deal_status} based on pricing, income durability, and debt coverage."
    )

    return {
        "deal_status": deal_status,
        "confidence_score": int(clamp((score * 0.65 + valuation_conf * 0.35), 0, 100)),
        "executive_summary": summary,
        "risk_analysis": {
            "critical_flags": unique_nonempty(critical_flags),
            "market_warnings": unique_nonempty(market_warnings)
        },
        "value_add_opportunities": unique_nonempty(value_add_opportunities),
        "algorithmic_score": score
    }


# ---------------------------------------------------------
# AI UNDERWRITER (ENHANCER)
# ---------------------------------------------------------
def analyze_with_gpt(listing_data, financial_data, computed_metrics, comps_data, property_specs, valuation_model, algorithmic_report):
    logging.info("🧠 Passing data to AI Underwriter...")

    if not openai_client:
        return algorithmic_report

    zillow_price = safe_float(listing_data.get('price') or listing_data.get('zestimate'))
    description = listing_data.get('description', 'No description provided.')
    rentcast_price = safe_float(financial_data.get('price'))
    avg_comp = safe_float(comps_data.get('average_comp_price'))

    prompt = f"""
    You are a cynical Senior Real Estate Underwriter specializing in the Dallas-Fort Worth (DFW) market.
    Improve the narrative and risk framing while respecting the deterministic underwriting baseline.

    PROPERTY ASSET:
    - {property_specs.get('bedrooms')} Beds, {property_specs.get('bathrooms')} Baths, {property_specs.get('sqft')} SqFt. Built in {property_specs.get('yearBuilt')}.

    RAW VALUATION DATA:
    - Zillow Price: ${zillow_price}
    - RentCast Valuation: ${rentcast_price}
    - Neighborhood Comp Average (based on {comps_data.get('comp_count')} recent sales): ${avg_comp}
    - Listing Description: "{description[:2500]}"

    RECONCILED VALUATION MODEL:
    - Estimated Value: ${valuation_model.get('estimated_value')}
    - Range: ${valuation_model.get('valuation_low')} to ${valuation_model.get('valuation_high')}
    - Price Delta vs Model: {valuation_model.get('price_vs_value_delta_pct')}%
    - Valuation Confidence: {valuation_model.get('confidence_score')}/100

    CALCULATED FINANCIAL METRICS:
    - NOI: ${computed_metrics.get('noi')}
    - Cap Rate: {computed_metrics.get('cap_rate')}%
    - DSCR: {computed_metrics.get('dscr')}
    - Cash Flow After Debt: ${computed_metrics.get('annual_cash_flow_after_debt')}
    - Data Quality Flag: {computed_metrics.get('data_quality_flag')}

    DETERMINISTIC BASELINE (trust this unless a clear contradiction is present):
    {json.dumps(algorithmic_report)}

    Critical instruction:
    - Do NOT describe missing metrics as dismal, stressed, non-performance, or zero income generation.
    - If rent, NOI, cap rate, or DSCR are missing because inputs are unavailable, explicitly state analysis is incomplete and requires manual review.

    You MUST return strictly valid JSON in this exact structure:
    {{
        "deal_status": "PASS or REJECT",
        "confidence_score": 0-100,
        "executive_summary": "Two sentence brutal summary.",
        "risk_analysis": {{
            "critical_flags": ["flag 1", "flag 2"],
            "market_warnings": ["warning 1"]
        }},
        "value_add_opportunities": ["opportunity 1", "opportunity 2"]
    }}
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        ai_data = json.loads(response.choices[0].message.content)

        merged = {
            "deal_status": ai_data.get("deal_status") if ai_data.get("deal_status") in {"PASS", "REJECT", "MANUAL_REVIEW"} else algorithmic_report.get("deal_status"),
            "confidence_score": int(clamp(safe_int(ai_data.get("confidence_score"), algorithmic_report.get("confidence_score")), 0, 100)),
            "executive_summary": ai_data.get("executive_summary") or algorithmic_report.get("executive_summary"),
            "risk_analysis": {
                "critical_flags": unique_nonempty(
                    (ai_data.get("risk_analysis", {}).get("critical_flags") or [])
                    + (algorithmic_report.get("risk_analysis", {}).get("critical_flags") or [])
                ),
                "market_warnings": unique_nonempty(
                    (ai_data.get("risk_analysis", {}).get("market_warnings") or [])
                    + (algorithmic_report.get("risk_analysis", {}).get("market_warnings") or [])
                )
            },
            "value_add_opportunities": unique_nonempty(
                (ai_data.get("value_add_opportunities") or [])
                + (algorithmic_report.get("value_add_opportunities") or [])
            ),
            "algorithmic_score": algorithmic_report.get("algorithmic_score")
        }

        # Keep hard guardrails from deterministic model.
        if algorithmic_report.get("deal_status") == "REJECT" and merged["deal_status"] != "REJECT":
            merged["deal_status"] = "REJECT"
        if algorithmic_report.get("deal_status") == "MANUAL_REVIEW":
            merged["deal_status"] = "MANUAL_REVIEW"

        return merged

    except Exception as e:
        logging.error(f"GPT Underwriter failed, using deterministic report: {e}")
        return algorithmic_report


# ---------------------------------------------------------
# API ENDPOINT
# ---------------------------------------------------------
@app.route(route="AnalyzeProperty", auth_level=func.AuthLevel.ANONYMOUS)
def AnalyzeProperty(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('🚀 PropScout Logic Engine triggered.')

    req_body = {}
    zillow_url = None
    address = None

    try:
        req_body = req.get_json()
    except ValueError:
        req_body = {}

    if isinstance(req_body, dict):
        zillow_url = req_body.get('url')
        address = req_body.get('address')

    # Fallback for clients sending query params or non-JSON body.
    if not zillow_url:
        zillow_url = req.params.get('url')
    if not address:
        address = req.params.get('address')

    if not zillow_url:
        return func.HttpResponse(
            json.dumps({
                "error": "Missing 'url'. Send JSON like: {\"url\":\"https://www.zillow.com/homedetails/.../\", \"address\":\"optional\"}"
            }),
            status_code=400,
            mimetype="application/json"
        )

    if not address:
        address = extract_address_from_url(zillow_url)
        if not address:
            return func.HttpResponse(
                json.dumps({"error": "Could not parse address from URL. Please provide it manually."}),
                status_code=400,
                mimetype="application/json"
            )

    report_id = f"{address.replace(' ', '-').replace(',', '').lower()}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M')}"

    financials = get_rentcast_data(address)
    neighborhood_comps = get_neighborhood_comps(address)
    listing_data = scrape_zillow(zillow_url)

    property_specs = {
        "bedrooms": listing_data.get('bedrooms', 'N/A'),
        "bathrooms": listing_data.get('bathrooms', 'N/A'),
        "sqft": listing_data.get('livingArea', 'N/A'),
        "yearBuilt": listing_data.get('yearBuilt', 'N/A')
    }

    listing_price = safe_float(listing_data.get('price'))
    fallback_price = safe_float(financials.get('price'))
    price = listing_price or fallback_price or 0

    rent_low = safe_float(financials.get('rentRange', {}).get('low'), default=0.0)
    rent_high = safe_float(financials.get('rentRange', {}).get('high'), default=0.0)
    zillow_rent_zestimate = safe_float(listing_data.get('rentZestimate'), default=0.0)
    history_rent = extract_rent_from_listing_history(listing_data)

    # Rent selection priority:
    # 1) RentCast range midpoint, 2) Zillow rentZestimate, 3) Zillow rent history fallback.
    monthly_rent = None
    if rent_low > 0 and rent_high > 0:
        monthly_rent = (rent_low + rent_high) / 2
    elif zillow_rent_zestimate > 0:
        monthly_rent = zillow_rent_zestimate
    elif history_rent and history_rent > 0:
        monthly_rent = history_rent

    valuation_model = build_valuation_model(listing_data, financials, neighborhood_comps, property_specs, monthly_rent)

    # Use modeled value as fallback purchase price when listing-side pricing is missing.
    if price <= 0:
        price = safe_float(valuation_model.get("estimated_value"))

    computed_metrics = calculate_financials(price, monthly_rent)
    algorithmic_report = run_algorithmic_underwrite(valuation_model, computed_metrics, neighborhood_comps, property_specs)
    ai_report = analyze_with_gpt(
        listing_data,
        financials,
        computed_metrics,
        neighborhood_comps,
        property_specs,
        valuation_model,
        algorithmic_report
    )

    final_report = {
        "id": report_id,
        "address": address,
        "property_specs": property_specs,
        "neighborhood_comps": neighborhood_comps,
        "raw_data_sources": {
            "rentcast_valuation": financials.get('price'),
            "zillow_price": listing_data.get('price'),
            "zillow_zestimate": listing_data.get('zestimate'),
            "rent_estimate_low": financials.get('rentRange', {}).get('low'),
            "rent_estimate_high": financials.get('rentRange', {}).get('high'),
            "zillow_rent_zestimate": listing_data.get('rentZestimate')
        },
        "valuation_model": valuation_model,
        "computed_financials": computed_metrics,
        "algorithmic_underwrite": algorithmic_report,
        "ai_underwriter": ai_report
    }

    try:
        if container:
            container.upsert_item(final_report)
    except Exception as e:
        logging.error(f"CosmosDB Save Failed: {e}")

    return func.HttpResponse(json.dumps(final_report, indent=4), mimetype="application/json")
