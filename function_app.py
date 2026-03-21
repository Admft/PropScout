import azure.functions as func
import datetime
import json
import logging
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from apify_client import ApifyClient
from azure.cosmos import CosmosClient, exceptions as cosmos_exceptions
from openai import OpenAI
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
RENTCAST_KEY = os.getenv("RENTCAST_API_KEY")
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
EXPECTED_API_KEY = os.getenv("PROPSCOUT_API_KEY")

COSMOS_DB_NAME = os.getenv("COSMOS_DB_NAME", "propscout-db")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME", "reports")
COSMOS_AUTO_CREATE = os.getenv("COSMOS_AUTO_CREATE", "false").lower() == "true"

REQUEST_TIMEOUT_SECONDS = 20
MAX_HTTP_RETRIES = 2
HTTP_BACKOFF_FACTOR = 0.4

# RentCast comps fetch tunables
COMP_RADIUS_MILES = 2
COMP_LIMIT = 12

# Financial assumptions
VACANCY_RATE = 0.05
PROPERTY_TAX_RATE = 0.022
INSURANCE_RATE = 0.005
MAINTENANCE_RATE = 0.010
MANAGEMENT_FEE_RATE = 0.08
CAPEX_RESERVE_RATE = 0.05
LTV = 0.80
MORTGAGE_RATE_ANNUAL = 0.07
AMORTIZATION_MONTHS = 360
TARGET_CAP_RATE = 0.0625

# Valuation tunables
OUTLIER_LOW_MULTIPLIER = 0.55
OUTLIER_HIGH_MULTIPLIER = 1.80
OUTLIER_WEIGHT_MULTIPLIER = 0.2

# Operational switches
FAST_MODE_SKIP_GPT = True
FAST_MODE_SKIP_PERSISTENCE = True

# ---------------------------------------------------------
# GLOBAL CLIENTS (LAZY INITIALIZED)
# ---------------------------------------------------------
_http_session: Optional[requests.Session] = None
_openai_client: Optional[OpenAI] = None
_apify_client: Optional[ApifyClient] = None
_cosmos_container = None
_cosmos_init_attempted = False


# ---------------------------------------------------------
# CORE HELPERS
# ---------------------------------------------------------
def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_float(value: Any, default: Optional[float] = 0.0) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def to_positive_float(value: Any) -> Optional[float]:
    parsed = safe_float(value, default=None)
    if parsed is None or parsed <= 0:
        return None
    return float(parsed)


def unique_nonempty(items: List[Any]) -> List[str]:
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


def build_report_id(address: str) -> str:
    address_slug = re.sub(r"[^a-z0-9]+", "-", (address or "unknown").lower()).strip("-")
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{address_slug[:60]}-{ts}-{uuid.uuid4().hex[:8]}"


def make_source_status(mode: str) -> Dict[str, Any]:
    return {
        "mode": mode,
        "rentcast_valuation": {"status": "unknown", "detail": None},
        "rentcast_comps": {"status": "unknown", "detail": None},
        "zillow_scrape": {"status": "unknown", "detail": None},
        "gpt_enhancement": {"status": "unknown", "detail": None},
        "persistence": {"status": "unknown", "detail": None},
        "rent_source": "none",
    }


def parse_bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


# ---------------------------------------------------------
# CLIENT INITIALIZATION
# ---------------------------------------------------------
def get_http_session() -> requests.Session:
    global _http_session
    if _http_session is not None:
        return _http_session

    session = requests.Session()
    retry = Retry(
        total=MAX_HTTP_RETRIES,
        connect=MAX_HTTP_RETRIES,
        read=MAX_HTTP_RETRIES,
        status=MAX_HTTP_RETRIES,
        backoff_factor=HTTP_BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    _http_session = session
    return _http_session


def get_openai_client() -> Optional[OpenAI]:
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    if not OPENAI_KEY:
        return None
    try:
        _openai_client = OpenAI(api_key=OPENAI_KEY)
        return _openai_client
    except Exception as exc:
        logging.error("openai_client_init_failed error=%s", exc)
        return None


def get_apify_client() -> Optional[ApifyClient]:
    global _apify_client
    if _apify_client is not None:
        return _apify_client
    if not APIFY_TOKEN:
        return None
    try:
        _apify_client = ApifyClient(APIFY_TOKEN)
        return _apify_client
    except Exception as exc:
        logging.error("apify_client_init_failed error=%s", exc)
        return None


def get_cosmos_container():
    global _cosmos_container, _cosmos_init_attempted
    if _cosmos_container is not None:
        return _cosmos_container
    if _cosmos_init_attempted:
        return None

    _cosmos_init_attempted = True
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        logging.warning("cosmos_not_configured")
        return None

    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        if COSMOS_AUTO_CREATE:
            db = client.create_database_if_not_exists(id=COSMOS_DB_NAME)
            _cosmos_container = db.create_container_if_not_exists(
                id=COSMOS_CONTAINER_NAME,
                partition_key={"paths": ["/id"], "kind": "Hash"},
            )
        else:
            db = client.get_database_client(COSMOS_DB_NAME)
            _cosmos_container = db.get_container_client(COSMOS_CONTAINER_NAME)
        logging.info("cosmos_container_ready db=%s container=%s", COSMOS_DB_NAME, COSMOS_CONTAINER_NAME)
        return _cosmos_container
    except cosmos_exceptions.CosmosResourceNotFoundError:
        logging.error("cosmos_resource_not_found db=%s container=%s", COSMOS_DB_NAME, COSMOS_CONTAINER_NAME)
        return None
    except Exception as exc:
        logging.error("cosmos_init_failed error=%s", exc)
        return None


# ---------------------------------------------------------
# VALIDATION & AUTH
# ---------------------------------------------------------
def enforce_api_key_if_configured(req: func.HttpRequest) -> Optional[func.HttpResponse]:
    if not EXPECTED_API_KEY:
        return None

    provided = req.headers.get("X-API-Key")
    if provided != EXPECTED_API_KEY:
        logging.warning("request_rejected invalid_api_key")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )
    return None


def validate_and_normalize_zillow_url(raw_url: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not raw_url:
        return None, "Missing 'url'."

    url = str(raw_url).strip()
    parsed = urlparse(url)

    if parsed.scheme.lower() != "https":
        return None, "URL must use https."

    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]

    if host != "zillow.com" and not host.endswith(".zillow.com"):
        return None, "Unsupported domain. Only Zillow URLs are allowed."

    path = parsed.path or ""
    if not path.startswith("/homedetails/"):
        return None, "Unsupported Zillow path. URL must be a homedetails page."

    if len(path.split("/")) < 3:
        return None, "Malformed Zillow homedetails URL."

    normalized = f"https://{parsed.netloc}{parsed.path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized, None


def extract_address_from_url(url: str) -> Optional[str]:
    logging.info("address_parse_attempt url=%s", url)
    parsed = urlparse(url)
    match = re.search(r"/homedetails/([^/]+)/", parsed.path)
    if not match:
        return None

    raw_string = match.group(1)
    clean_address = raw_string.replace("-", " ").strip()
    logging.info("address_parse_success address=%s", clean_address)
    return clean_address or None


# ---------------------------------------------------------
# EXTERNAL DATA PIPELINE
# ---------------------------------------------------------
def get_rentcast_data(address: str) -> Tuple[Dict[str, Any], str, Optional[str]]:
    if not RENTCAST_KEY:
        return {}, "skipped", "RENTCAST_API_KEY not configured"

    url = "https://api.rentcast.io/v1/avm/value"
    params = {"address": address, "propertyType": "Single Family"}
    headers = {"accept": "application/json", "X-Api-Key": RENTCAST_KEY}

    try:
        response = get_http_session().get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code == 200:
            payload = response.json()
            return payload if isinstance(payload, dict) else {}, "ok", None
        return {}, "failed", f"http_{response.status_code}"
    except requests.RequestException as exc:
        return {}, "failed", f"network_error: {exc}"
    except Exception as exc:
        return {}, "failed", f"unexpected_error: {exc}"


def get_neighborhood_comps(address: str) -> Tuple[Dict[str, Any], str, Optional[str]]:
    default_comps = {
        "average_comp_price": None,
        "median_comp_price": None,
        "comp_count": 0,
        "average_comp_price_per_sqft": None,
        "comps": [],
    }

    if not RENTCAST_KEY:
        return default_comps, "skipped", "RENTCAST_API_KEY not configured"

    url = "https://api.rentcast.io/v1/sales/comps"
    params = {
        "address": address,
        "propertyType": "Single Family",
        "radius": COMP_RADIUS_MILES,
        "limit": COMP_LIMIT,
    }
    headers = {"accept": "application/json", "X-Api-Key": RENTCAST_KEY}

    try:
        response = get_http_session().get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code != 200:
            return default_comps, "failed", f"http_{response.status_code}"

        comps = response.json()
        if not isinstance(comps, list):
            return default_comps, "failed", "invalid_payload_shape"

        clean_comps = []
        prices = []
        ppsf_values = []

        for comp in comps:
            if not isinstance(comp, dict):
                continue

            price = to_positive_float(comp.get("price"))
            sqft = to_positive_float(comp.get("squareFootage") or comp.get("livingArea"))
            distance = to_positive_float(comp.get("distance"))
            if price is None:
                continue

            prices.append(price)
            ppsf = None
            if sqft is not None and sqft > 0:
                ppsf = price / sqft
                ppsf_values.append(ppsf)

            clean_comps.append(
                {
                    "price": round(price, 2),
                    "square_footage": round(sqft, 2) if sqft is not None else None,
                    "distance_miles": round(distance, 2) if distance is not None else None,
                    "price_per_sqft": round(ppsf, 2) if ppsf is not None else None,
                    "sold_date": comp.get("soldDate"),
                }
            )

        if not prices:
            return default_comps, "failed", "no_usable_comp_prices"

        avg_comp = sum(prices) / len(prices)
        sorted_prices = sorted(prices)
        mid = len(sorted_prices) // 2
        if len(sorted_prices) % 2 == 0:
            median_comp = (sorted_prices[mid - 1] + sorted_prices[mid]) / 2
        else:
            median_comp = sorted_prices[mid]

        avg_ppsf = (sum(ppsf_values) / len(ppsf_values)) if ppsf_values else None

        return (
            {
                "average_comp_price": round(avg_comp, 2),
                "median_comp_price": round(median_comp, 2),
                "comp_count": len(prices),
                "average_comp_price_per_sqft": round(avg_ppsf, 2) if avg_ppsf is not None else None,
                "comps": clean_comps[:8],
            },
            "ok",
            None,
        )
    except requests.RequestException as exc:
        return default_comps, "failed", f"network_error: {exc}"
    except Exception as exc:
        return default_comps, "failed", f"unexpected_error: {exc}"


def scrape_zillow(zillow_url: str) -> Tuple[Dict[str, Any], str, Optional[str]]:
    client = get_apify_client()
    if client is None:
        return {}, "skipped", "APIFY_API_TOKEN not configured"

    run_input = {"startUrls": [{"url": zillow_url}], "maxItems": 1}

    for attempt in range(1, 3):
        try:
            run = client.actor("maxcopell/zillow-detail-scraper").call(run_input=run_input)
            dataset = client.dataset(run["defaultDatasetId"]).list_items().items
            if dataset and isinstance(dataset, list) and isinstance(dataset[0], dict):
                return dataset[0], "ok", None
            return {}, "failed", "empty_dataset"
        except Exception as exc:
            if attempt == 2:
                return {}, "failed", f"apify_error: {exc}"
            time.sleep(0.6 * attempt)

    return {}, "failed", "unknown_apify_failure"


# ---------------------------------------------------------
# RENT EXTRACTION HELPERS
# ---------------------------------------------------------
def parse_rent_amount(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        amount = float(value)
    elif isinstance(value, str):
        cleaned = re.sub(r"[^\d.]", "", value)
        if not cleaned:
            return None
        amount = safe_float(cleaned, default=0.0) or 0.0
    else:
        return None

    # Guardrail against implausible monthly rent values.
    if amount <= 0 or amount < 300 or amount > 50000:
        return None
    return amount


def extract_rent_from_listing_history(listing_data: Dict[str, Any]) -> Optional[float]:
    """
    Best-effort extraction from history-like arrays in inconsistent Zillow payloads.
    This is intentionally conservative and transparent rather than schema-fragile.
    """
    if not isinstance(listing_data, dict):
        return None

    history_lists = []
    for key, value in listing_data.items():
        key_l = str(key).lower()
        if isinstance(value, list) and any(token in key_l for token in ("history", "event", "price")):
            history_lists.append(value)

    rent_keywords = ("rent", "rental", "leased", "lease")
    rent_value_keys = ("rent", "rentalPrice", "monthlyRent", "price", "listPrice", "amount")
    date_keys = ("date", "eventDate", "postedDate", "time", "datetime")

    candidates: List[Tuple[int, int, float]] = []

    for history in history_lists:
        if not isinstance(history, list):
            continue

        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                continue

            text_blob = " ".join(
                str(item.get(k, "")).lower()
                for k in ("event", "eventType", "type", "description", "status", "source")
            )
            has_rent_signal = any(keyword in text_blob for keyword in rent_keywords)
            if not has_rent_signal:
                continue

            amount = None
            for k in rent_value_keys:
                amount = parse_rent_amount(item.get(k))
                if amount is not None:
                    break
                # Some scrapers emit title case/upper variants.
                amount = parse_rent_amount(item.get(k.title()) or item.get(k.upper()))
                if amount is not None:
                    break

            if amount is None:
                continue

            recency = 0
            for dkey in date_keys:
                raw = item.get(dkey)
                if raw is None:
                    continue
                digits = re.sub(r"\D", "", str(raw))
                if len(digits) >= 8:
                    recency = max(recency, safe_int(digits[:14], 0))

            candidates.append((recency, idx, amount))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return round(candidates[0][2], 2)


# ---------------------------------------------------------
# VALUATION ENGINE
# ---------------------------------------------------------
def build_valuation_model(
    listing_data: Dict[str, Any],
    financial_data: Dict[str, Any],
    comps_data: Dict[str, Any],
    property_specs: Dict[str, Any],
    monthly_rent: Optional[float],
) -> Dict[str, Any]:
    listing_price = to_positive_float(listing_data.get("price"))
    zestimate = to_positive_float(listing_data.get("zestimate"))
    rentcast_price = to_positive_float(financial_data.get("price"))
    comp_avg = to_positive_float(comps_data.get("average_comp_price"))
    comp_median = to_positive_float(comps_data.get("median_comp_price"))
    comp_ppsf = to_positive_float(comps_data.get("average_comp_price_per_sqft"))
    sqft = to_positive_float(property_specs.get("sqft"))
    year_built = safe_int(property_specs.get("yearBuilt"), 0)

    has_rent = monthly_rent is not None and monthly_rent > 0
    signals = []

    if listing_price is not None:
        signals.append({"name": "zillow_list_price", "value": listing_price, "weight": 0.22})
    if zestimate is not None:
        signals.append({"name": "zillow_zestimate", "value": zestimate, "weight": 0.12})
    if rentcast_price is not None:
        signals.append({"name": "rentcast_avm", "value": rentcast_price, "weight": 0.34})
    if comp_median is not None:
        signals.append({"name": "comps_median", "value": comp_median, "weight": 0.22})
    if comp_avg is not None:
        signals.append({"name": "comps_average", "value": comp_avg, "weight": 0.14})

    if comp_ppsf is not None and sqft is not None:
        signals.append({"name": "comps_price_per_sqft", "value": comp_ppsf * sqft, "weight": 0.18})

    if has_rent:
        annual_gross = monthly_rent * 12
        expense_ratio = 0.38
        if year_built and year_built < 1990:
            expense_ratio += 0.03
        elif year_built and year_built > 2018:
            expense_ratio -= 0.02

        implied_noi = annual_gross * (1 - clamp(expense_ratio, 0.30, 0.50))
        rent_based_value = implied_noi / TARGET_CAP_RATE if TARGET_CAP_RATE > 0 else None
        if rent_based_value and rent_based_value > 0:
            signals.append({"name": "income_approach", "value": rent_based_value, "weight": 0.20})

    values = [s["value"] for s in signals if s.get("value") is not None and s["value"] > 0]
    if not values:
        return {
            "estimated_value": None,
            "valuation_low": None,
            "valuation_high": None,
            "confidence_score": 25,
            "price_vs_value_delta": None,
            "price_vs_value_delta_pct": None,
            "valuation_status": "unknown",
            "suggested_offer": None,
            "signals": [],
        }

    sorted_values = sorted(values)
    mid = len(sorted_values) // 2
    center = (sorted_values[mid - 1] + sorted_values[mid]) / 2 if len(sorted_values) % 2 == 0 else sorted_values[mid]

    for signal in signals:
        val = signal["value"]
        if val < center * OUTLIER_LOW_MULTIPLIER or val > center * OUTLIER_HIGH_MULTIPLIER:
            signal["outlier"] = True
            signal["adjusted_weight"] = signal["weight"] * OUTLIER_WEIGHT_MULTIPLIER
        else:
            signal["outlier"] = False
            signal["adjusted_weight"] = signal["weight"]

    weight_sum = sum(s["adjusted_weight"] for s in signals)
    estimate = center if weight_sum <= 0 else sum(s["value"] * s["adjusted_weight"] for s in signals) / weight_sum

    variance = 0.0
    if weight_sum > 0:
        variance = sum(s["adjusted_weight"] * ((s["value"] - estimate) ** 2) for s in signals) / weight_sum

    std_dev = variance ** 0.5
    dispersion_ratio = (std_dev / estimate) if estimate > 0 else 1.0

    comp_count = safe_int(comps_data.get("comp_count"), 0)
    confidence = 84
    confidence -= min(30, int(dispersion_ratio * 100))
    confidence -= 6 if len(signals) < 4 else 0
    confidence -= 8 if comp_count < 3 else 0
    confidence -= 6 if not has_rent else 0
    confidence -= 5 if rentcast_price is None else 0
    confidence += 4 if len(signals) >= 6 else 0
    confidence = int(clamp(confidence, 25, 95))

    range_pct = 0.07 + min(0.18, dispersion_ratio * 0.9)
    if confidence < 55:
        range_pct += 0.05

    valuation_low = estimate * (1 - range_pct)
    valuation_high = estimate * (1 + range_pct)

    ask_price = listing_price or rentcast_price
    delta = (ask_price - estimate) if ask_price is not None else None
    delta_pct = ((delta / estimate) * 100) if ask_price is not None and estimate > 0 else None

    if ask_price is None:
        valuation_status = "unknown"
    elif delta_pct is not None and delta_pct >= 12:
        valuation_status = "overpriced"
    elif delta_pct is not None and delta_pct >= 5:
        valuation_status = "slightly_overpriced"
    elif delta_pct is not None and delta_pct <= -10:
        valuation_status = "undervalued"
    elif delta_pct is not None and delta_pct <= -4:
        valuation_status = "slightly_undervalued"
    else:
        valuation_status = "fair_value"

    suggested_offer = estimate * (0.96 if confidence >= 70 else 0.92) if estimate > 0 else None

    return {
        "estimated_value": round(estimate, 2),
        "valuation_low": round(valuation_low, 2),
        "valuation_high": round(valuation_high, 2),
        "confidence_score": confidence,
        "price_vs_value_delta": round(delta, 2) if delta is not None else None,
        "price_vs_value_delta_pct": round(delta_pct, 2) if delta_pct is not None else None,
        "valuation_status": valuation_status,
        "suggested_offer": round(suggested_offer, 2) if suggested_offer is not None else None,
        "signals": [
            {
                "name": s["name"],
                "value": round(s["value"], 2),
                "base_weight": round(s["weight"], 3),
                "adjusted_weight": round(s["adjusted_weight"], 3),
                "outlier": s["outlier"],
            }
            for s in signals
        ],
    }


# ---------------------------------------------------------
# FINANCIAL ENGINE
# ---------------------------------------------------------
def calculate_financials(price: Optional[float], monthly_rent: Optional[float]) -> Dict[str, Any]:
    logging.info("financials_compute_start")

    has_price = price is not None and price > 0
    has_rent = monthly_rent is not None and monthly_rent > 0

    # Missing rent/price means incomputable metrics, not zero business performance.
    if not has_price or not has_rent:
        if has_price and not has_rent:
            quality = "missing_rent"
        elif not has_price and not has_rent:
            quality = "missing_price_and_rent"
        else:
            quality = "missing_price"

        return {
            "purchase_price": round(price, 2) if has_price else None,
            "monthly_rent_est": round(monthly_rent, 2) if has_rent else None,
            "annual_gross_rent": None,
            "annual_expenses_est": None,
            "noi": None,
            "cap_rate": None,
            "dscr": None,
            "annual_debt_service": None,
            "annual_cash_flow_after_debt": None,
            "breakeven_occupancy": None,
            "data_quality_flag": quality,
        }

    annual_gross_rent = monthly_rent * 12
    vacancy = annual_gross_rent * VACANCY_RATE
    effective_gross_income = annual_gross_rent - vacancy

    taxes = price * PROPERTY_TAX_RATE
    insurance = price * INSURANCE_RATE
    maintenance = price * MAINTENANCE_RATE
    capex_reserve = annual_gross_rent * CAPEX_RESERVE_RATE
    property_mgmt = effective_gross_income * MANAGEMENT_FEE_RATE

    annual_expenses = taxes + insurance + maintenance + capex_reserve + property_mgmt
    noi = effective_gross_income - annual_expenses
    cap_rate = (noi / price) * 100 if price > 0 else None

    principal = price * LTV
    monthly_rate = MORTGAGE_RATE_ANNUAL / 12
    n = AMORTIZATION_MONTHS

    monthly_mortgage = principal * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)
    annual_debt_service = monthly_mortgage * 12

    dscr = noi / annual_debt_service if annual_debt_service > 0 else None
    annual_cash_flow_after_debt = noi - annual_debt_service
    breakeven_occupancy = (annual_expenses + annual_debt_service) / annual_gross_rent if annual_gross_rent > 0 else None

    return {
        "purchase_price": round(price, 2),
        "monthly_rent_est": round(monthly_rent, 2),
        "annual_gross_rent": round(annual_gross_rent, 2),
        "annual_expenses_est": round(annual_expenses, 2),
        "noi": round(noi, 2),
        "cap_rate": round(cap_rate, 2) if cap_rate is not None else None,
        "dscr": round(dscr, 2) if dscr is not None else None,
        "annual_debt_service": round(annual_debt_service, 2),
        "annual_cash_flow_after_debt": round(annual_cash_flow_after_debt, 2),
        "breakeven_occupancy": round(breakeven_occupancy * 100, 2) if breakeven_occupancy is not None else None,
        "data_quality_flag": "ok",
    }


# ---------------------------------------------------------
# DETERMINISTIC UNDERWRITER
# ---------------------------------------------------------
def run_algorithmic_underwrite(
    valuation_model: Dict[str, Any],
    financial_metrics: Dict[str, Any],
    comps_data: Dict[str, Any],
    property_specs: Dict[str, Any],
) -> Dict[str, Any]:
    score = 100
    critical_flags = []
    market_warnings = []
    value_add_opportunities = []

    cap_rate = financial_metrics.get("cap_rate")
    dscr = financial_metrics.get("dscr")
    cash_flow = financial_metrics.get("annual_cash_flow_after_debt")
    breakeven = financial_metrics.get("breakeven_occupancy")
    quality = financial_metrics.get("data_quality_flag")

    valuation_conf = safe_int(valuation_model.get("confidence_score"), 25)
    price_delta_pct = valuation_model.get("price_vs_value_delta_pct")
    valuation_status = valuation_model.get("valuation_status", "unknown")
    comp_count = safe_int(comps_data.get("comp_count"), 0)
    year_built = safe_int(property_specs.get("yearBuilt"), 0)

    missing_financials = quality in {"missing_rent", "missing_price", "missing_price_and_rent"} or any(
        metric is None for metric in [cap_rate, dscr, cash_flow, breakeven]
    )

    # Missing rent/price should route to manual review rather than fake operational distress.
    if missing_financials:
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

    if valuation_status in {"overpriced", "slightly_overpriced"} and price_delta_pct is not None:
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

    if missing_financials:
        deal_status = "MANUAL_REVIEW"
        logging.info("underwrite_manual_review reason=missing_financials data_quality_flag=%s", quality)
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
            "market_warnings": unique_nonempty(market_warnings),
        },
        "value_add_opportunities": unique_nonempty(value_add_opportunities),
        "algorithmic_score": score,
    }


# ---------------------------------------------------------
# AI ENHANCER
# ---------------------------------------------------------
def analyze_with_gpt(
    listing_data: Dict[str, Any],
    financial_data: Dict[str, Any],
    computed_metrics: Dict[str, Any],
    comps_data: Dict[str, Any],
    property_specs: Dict[str, Any],
    valuation_model: Dict[str, Any],
    algorithmic_report: Dict[str, Any],
) -> Tuple[Dict[str, Any], str, Optional[str]]:
    client = get_openai_client()
    if client is None:
        return algorithmic_report, "skipped", "OPENAI_API_KEY not configured"

    zillow_price = listing_data.get("price") or listing_data.get("zestimate")
    rentcast_price = financial_data.get("price")
    avg_comp = comps_data.get("average_comp_price")
    description = listing_data.get("description", "No description provided.")

    prompt = f"""
You are a cynical Senior Real Estate Underwriter specializing in the Dallas-Fort Worth (DFW) market.
Improve the narrative and risk framing while respecting the deterministic underwriting baseline.

PROPERTY ASSET:
- {property_specs.get('bedrooms')} Beds, {property_specs.get('bathrooms')} Baths, {property_specs.get('sqft')} SqFt. Built in {property_specs.get('yearBuilt')}.

RAW VALUATION DATA:
- Zillow Price: {zillow_price}
- RentCast Valuation: {rentcast_price}
- Neighborhood Comp Average (based on {comps_data.get('comp_count')} recent sales): {avg_comp}
- Listing Description: "{str(description)[:2500]}"

RECONCILED VALUATION MODEL:
- Estimated Value: {valuation_model.get('estimated_value')}
- Range: {valuation_model.get('valuation_low')} to {valuation_model.get('valuation_high')}
- Price Delta vs Model: {valuation_model.get('price_vs_value_delta_pct')}%
- Valuation Confidence: {valuation_model.get('confidence_score')}/100

CALCULATED FINANCIAL METRICS:
- NOI: {computed_metrics.get('noi')}
- Cap Rate: {computed_metrics.get('cap_rate')}%
- DSCR: {computed_metrics.get('dscr')}
- Cash Flow After Debt: {computed_metrics.get('annual_cash_flow_after_debt')}
- Data Quality Flag: {computed_metrics.get('data_quality_flag')}

DETERMINISTIC BASELINE (source of truth unless clear data contradiction):
{json.dumps(algorithmic_report)}

Critical instructions:
- Do NOT describe missing metrics as dismal, stressed, non-performance, or zero income generation.
- If rent, NOI, cap rate, or DSCR are missing because inputs are unavailable, explicitly state analysis is incomplete and requires manual review.
- Valid deal_status values are strictly: PASS, REJECT, MANUAL_REVIEW.

Return strictly valid JSON in this exact structure:
{{
  "deal_status": "PASS or REJECT or MANUAL_REVIEW",
  "confidence_score": 0-100,
  "executive_summary": "Two sentence brutal summary.",
  "risk_analysis": {{
    "critical_flags": ["flag 1", "flag 2"],
    "market_warnings": ["warning 1"]
  }},
  "value_add_opportunities": ["opportunity 1", "opportunity 2"]
}}
"""

    for attempt in range(1, 3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You output strictly valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            payload = json.loads(response.choices[0].message.content)

            merged = {
                "deal_status": payload.get("deal_status")
                if payload.get("deal_status") in {"PASS", "REJECT", "MANUAL_REVIEW"}
                else algorithmic_report.get("deal_status"),
                "confidence_score": int(
                    clamp(
                        safe_int(payload.get("confidence_score"), algorithmic_report.get("confidence_score")),
                        0,
                        100,
                    )
                ),
                "executive_summary": payload.get("executive_summary") or algorithmic_report.get("executive_summary"),
                "risk_analysis": {
                    "critical_flags": unique_nonempty(
                        (payload.get("risk_analysis", {}).get("critical_flags") or [])
                        + (algorithmic_report.get("risk_analysis", {}).get("critical_flags") or [])
                    ),
                    "market_warnings": unique_nonempty(
                        (payload.get("risk_analysis", {}).get("market_warnings") or [])
                        + (algorithmic_report.get("risk_analysis", {}).get("market_warnings") or [])
                    ),
                },
                "value_add_opportunities": unique_nonempty(
                    (payload.get("value_add_opportunities") or [])
                    + (algorithmic_report.get("value_add_opportunities") or [])
                ),
                "algorithmic_score": algorithmic_report.get("algorithmic_score"),
            }

            # Deterministic guardrails remain authoritative.
            if algorithmic_report.get("deal_status") == "REJECT" and merged["deal_status"] != "REJECT":
                merged["deal_status"] = "REJECT"
            if algorithmic_report.get("deal_status") == "MANUAL_REVIEW":
                merged["deal_status"] = "MANUAL_REVIEW"

            return merged, "ok", None
        except Exception as exc:
            if attempt == 2:
                logging.error("gpt_enhancement_failed error=%s", exc)
                return algorithmic_report, "failed", f"gpt_error: {exc}"
            time.sleep(0.8 * attempt)

    return algorithmic_report, "failed", "unknown_gpt_error"


# ---------------------------------------------------------
# API ENDPOINT
# ---------------------------------------------------------
@app.route(route="AnalyzeProperty", auth_level=func.AuthLevel.ANONYMOUS)
def AnalyzeProperty(req: func.HttpRequest) -> func.HttpResponse:
    request_id = uuid.uuid4().hex[:10]
    logging.info("request_start request_id=%s", request_id)

    auth_error = enforce_api_key_if_configured(req)
    if auth_error:
        return auth_error

    req_body: Dict[str, Any] = {}
    try:
        parsed = req.get_json()
        if isinstance(parsed, dict):
            req_body = parsed
    except ValueError:
        req_body = {}

    mode_raw = req_body.get("mode") if req_body else None
    if mode_raw is None:
        mode_raw = req.params.get("mode")
    mode = "fast" if str(mode_raw or "").strip().lower() == "fast" else "full"

    source_status = make_source_status(mode)

    zillow_url_input = (req_body.get("url") if req_body else None) or req.params.get("url")
    manual_address = (req_body.get("address") if req_body else None) or req.params.get("address")

    zillow_url, validation_error = validate_and_normalize_zillow_url(zillow_url_input)
    if validation_error:
        logging.warning("request_validation_failed request_id=%s error=%s", request_id, validation_error)
        return func.HttpResponse(
            json.dumps({"error": validation_error}),
            status_code=400,
            mimetype="application/json",
        )

    address = str(manual_address).strip() if manual_address else extract_address_from_url(zillow_url)
    if not address:
        logging.warning("address_resolution_failed request_id=%s", request_id)
        return func.HttpResponse(
            json.dumps({"error": "Could not derive address from URL. Provide 'address' manually."}),
            status_code=400,
            mimetype="application/json",
        )

    report_id = build_report_id(address)

    financials, val_status, val_detail = get_rentcast_data(address)
    source_status["rentcast_valuation"] = {"status": val_status, "detail": val_detail}
    logging.info("rentcast_valuation status=%s detail=%s", val_status, val_detail)

    neighborhood_comps, comps_status, comps_detail = get_neighborhood_comps(address)
    source_status["rentcast_comps"] = {"status": comps_status, "detail": comps_detail}
    logging.info("rentcast_comps status=%s detail=%s", comps_status, comps_detail)

    listing_data, z_status, z_detail = scrape_zillow(zillow_url)
    source_status["zillow_scrape"] = {"status": z_status, "detail": z_detail}
    logging.info("zillow_scrape status=%s detail=%s", z_status, z_detail)

    property_specs = {
        "bedrooms": listing_data.get("bedrooms"),
        "bathrooms": listing_data.get("bathrooms"),
        "sqft": listing_data.get("livingArea"),
        "yearBuilt": listing_data.get("yearBuilt"),
    }

    listing_price = to_positive_float(listing_data.get("price"))
    rentcast_price = to_positive_float(financials.get("price"))
    fallback_price = listing_price or rentcast_price

    rent_low = to_positive_float((financials.get("rentRange") or {}).get("low"))
    rent_high = to_positive_float((financials.get("rentRange") or {}).get("high"))
    rent_zestimate = to_positive_float(listing_data.get("rentZestimate"))
    history_rent = extract_rent_from_listing_history(listing_data)

    # Rent source priority: RentCast midpoint > Zillow rentZestimate > Zillow history > none.
    monthly_rent = None
    if rent_low is not None and rent_high is not None:
        monthly_rent = (rent_low + rent_high) / 2
        source_status["rent_source"] = "rentcast_midpoint"
    elif rent_zestimate is not None:
        monthly_rent = rent_zestimate
        source_status["rent_source"] = "zillow_rent_zestimate"
    elif history_rent is not None:
        monthly_rent = history_rent
        source_status["rent_source"] = "zillow_history"
    else:
        source_status["rent_source"] = "none"

    if source_status["rent_source"] != "rentcast_midpoint":
        logging.info("rent_fallback_used source=%s", source_status["rent_source"])

    valuation_model = build_valuation_model(
        listing_data=listing_data,
        financial_data=financials,
        comps_data=neighborhood_comps,
        property_specs=property_specs,
        monthly_rent=monthly_rent,
    )

    price = fallback_price or to_positive_float(valuation_model.get("estimated_value"))
    computed_metrics = calculate_financials(price, monthly_rent)

    algorithmic_report = run_algorithmic_underwrite(
        valuation_model=valuation_model,
        financial_metrics=computed_metrics,
        comps_data=neighborhood_comps,
        property_specs=property_specs,
    )

    if mode == "fast" and FAST_MODE_SKIP_GPT:
        ai_report = algorithmic_report
        source_status["gpt_enhancement"] = {"status": "skipped", "detail": "fast_mode"}
    else:
        ai_report, gpt_status, gpt_detail = analyze_with_gpt(
            listing_data=listing_data,
            financial_data=financials,
            computed_metrics=computed_metrics,
            comps_data=neighborhood_comps,
            property_specs=property_specs,
            valuation_model=valuation_model,
            algorithmic_report=algorithmic_report,
        )
        source_status["gpt_enhancement"] = {"status": gpt_status, "detail": gpt_detail}

    final_report = {
        "id": report_id,
        "address": address,
        "property_specs": property_specs,
        "neighborhood_comps": neighborhood_comps,
        "raw_data_sources": {
            "rentcast_valuation": financials.get("price"),
            "zillow_price": listing_data.get("price"),
            "zillow_zestimate": listing_data.get("zestimate"),
            "rent_estimate_low": (financials.get("rentRange") or {}).get("low"),
            "rent_estimate_high": (financials.get("rentRange") or {}).get("high"),
            "zillow_rent_zestimate": listing_data.get("rentZestimate"),
            "zillow_history_rent_estimate": history_rent,
        },
        "valuation_model": valuation_model,
        "computed_financials": computed_metrics,
        "algorithmic_underwrite": algorithmic_report,
        "ai_underwriter": ai_report,
        "source_status": source_status,
    }

    should_persist = not (mode == "fast" and FAST_MODE_SKIP_PERSISTENCE)
    if should_persist:
        container = get_cosmos_container()
        if container is None:
            source_status["persistence"] = {"status": "skipped", "detail": "cosmos_not_available"}
        else:
            try:
                container.upsert_item(final_report)
                source_status["persistence"] = {"status": "ok", "detail": None}
            except Exception as exc:
                logging.error("cosmos_persist_failed request_id=%s error=%s", request_id, exc)
                source_status["persistence"] = {"status": "failed", "detail": str(exc)}
    else:
        source_status["persistence"] = {"status": "skipped", "detail": "fast_mode"}

    return func.HttpResponse(json.dumps(final_report, indent=4), mimetype="application/json")
