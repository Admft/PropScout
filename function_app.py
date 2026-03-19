import azure.functions as func
import logging
import json
import os
import requests
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

# Initialize Clients
try:
    openai_client = OpenAI(api_key=OPENAI_KEY)
    db_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    # Reverted back to your original working database name!
    database = db_client.create_database_if_not_exists(id="propscout-db") 
    container = database.create_container_if_not_exists(id="reports", partition_key=PartitionKey(path="/id"))
    print("✅ Successfully connected to Cosmos DB!")
except Exception as e:
    print(f"❌ CRITICAL ERROR ON STARTUP: {e}")
    container = None

# ---------------------------------------------------------
# DATA PIPELINE
# ---------------------------------------------------------
def get_rentcast_data(address):
    logging.info(f"📡 Fetching RentCast data for: {address}")
    url = "https://api.rentcast.io/v1/avm/value"
    params = {"address": address, "propertyType": "Single Family"}
    headers = {"accept": "application/json", "X-Api-Key": RENTCAST_KEY}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logging.error(f"RentCast Failed: {e}")
    return {}

def scrape_zillow(zillow_url):
    logging.info(f"🕷️ Scraping Zillow: {zillow_url}")
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
# FINANCIAL ENGINE (THE HARD MATH)
# ---------------------------------------------------------
def calculate_financials(price, monthly_rent):
    logging.info("🧮 Crunching hard financial metrics...")
    
    if not price or not monthly_rent or price == 0:
        return {"error": "Missing price or rent to calculate metrics."}

    annual_rent = monthly_rent * 12
    
    # North Texas Expense Assumptions
    taxes = price * 0.022      # ~2.2% standard Collin/Dallas County
    insurance = price * 0.005  # 0.5% standard
    maintenance = price * 0.01 # 1% standard
    property_mgmt = annual_rent * 0.08 # 8% management fee
    
    annual_expenses = taxes + insurance + maintenance + property_mgmt
    noi = annual_rent - annual_expenses
    cap_rate = (noi / price) * 100
    
    # DSCR Calculation: Assume 20% down, 7% interest, 30-year fixed
    principal = price * 0.80
    monthly_rate = 0.07 / 12
    n_payments = 360
    monthly_mortgage = principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    annual_debt_service = monthly_mortgage * 12
    
    dscr = noi / annual_debt_service if annual_debt_service > 0 else 0

    return {
        "purchase_price": round(price, 2),
        "monthly_rent_est": round(monthly_rent, 2),
        "annual_expenses_est": round(annual_expenses, 2),
        "noi": round(noi, 2),
        "cap_rate": round(cap_rate, 2),
        "dscr": round(dscr, 2)
    }

# ---------------------------------------------------------
# AI UNDERWRITER (STRUCTURED OUTPUT)
# ---------------------------------------------------------
def analyze_with_gpt(listing_data, financial_data, computed_metrics):
    logging.info("🧠 Passing data to AI Underwriter...")
    
    zillow_price = listing_data.get('price') or listing_data.get('zestimate') or 0
    description = listing_data.get('description', 'No description provided.')
    rentcast_price = financial_data.get('price', 0)

    prompt = f"""
    You are a cynical Senior Real Estate Underwriter specializing in the Dallas-Fort Worth (DFW) market.
    Analyze this property strictly based on the provided hard math and description.

    RAW DATA:
    - Zillow Price: ${zillow_price}
    - RentCast Valuation: ${rentcast_price}
    - Listing Description: "{description[:2500]}"

    CALCULATED FINANCIAL METRICS:
    - Net Operating Income (NOI): ${computed_metrics.get('noi')}
    - Cap Rate: {computed_metrics.get('cap_rate')}%
    - Debt Service Coverage Ratio (DSCR): {computed_metrics.get('dscr')}

    YOUR MISSION:
    1. Financial Reality: A Cap Rate under 5% or a DSCR under 1.20 is highly risky for an enterprise investor. Flag this immediately.
    2. DFW Specific Risks: Scan the description for foundation issues ("pier and beam", "settling"), roof/hail damage, and flood risks.
    3. Valuation Variance: Note any major discrepancy between the Zillow Price and RentCast value.

    You MUST return your analysis in the exact JSON structure below. Do not deviate.
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
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
    
# ---------------------------------------------------------
# API ENDPOINT
# ---------------------------------------------------------
@app.route(route="AnalyzeProperty", auth_level=func.AuthLevel.ANONYMOUS)
def AnalyzeProperty(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('🚀 YieldLens Logic Engine triggered.')

    try:
        req_body = req.get_json()
        zillow_url = req_body.get('url')
        address = req_body.get('address') 
    except ValueError:
        return func.HttpResponse(json.dumps({"error": "Invalid JSON payload"}), status_code=400, mimetype="application/json")

    if not zillow_url or not address:
        return func.HttpResponse(json.dumps({"error": "Missing 'url' or 'address'"}), status_code=400, mimetype="application/json")

    report_id = address.replace(" ", "-").replace(",", "").lower()

    # Pipeline execution
    financials = get_rentcast_data(address)
    listing_data = scrape_zillow(zillow_url)
    
    # Extract data for math
    price = listing_data.get('price') or financials.get('price') or 0
    rent_low = financials.get('rentRange', {}).get('low', 0)
    rent_high = financials.get('rentRange', {}).get('high', 0)
    monthly_rent = (rent_low + rent_high) / 2 if rent_low and rent_high else 0

    computed_metrics = calculate_financials(price, monthly_rent)

    ai_report = analyze_with_gpt(listing_data, financials, computed_metrics)

    # Compile the Enterprise Report
    final_report = {
        "id": report_id,
        "address": address,
        "raw_data_sources": {
            "rentcast_valuation": financials.get('price'),
            "zillow_price": listing_data.get('price')
        },
        "computed_financials": computed_metrics,
        "ai_underwriter": ai_report
    }
    
    try:
        container.upsert_item(final_report)
    except Exception as e:
        logging.error(f"CosmosDB Save Failed: {e}")

    return func.HttpResponse(json.dumps(final_report, indent=4), mimetype="application/json")