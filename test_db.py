import os
import requests
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load secrets
load_dotenv()
RENTCAST_KEY = os.getenv("RENTCAST_API_KEY")
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")

# ---------------------------------------------------------
# DFW MARKET CONFIGURATION (Wylie, TX)
# ---------------------------------------------------------
# We are testing with a real active/sold listing in Wylie to prove DFW compatibility.
TEST_ADDRESS = "1200 Woodbridge Pkwy, Wylie, TX 75098"
TEST_ZILLOW_URL = "https://www.zillow.com/homedetails/1200-Woodbridge-Pkwy-Wylie-TX-75098/26936553_zpid/"

def test_dfw_financials():
    print(f"\n📡 [1/2] Fetching DFW Financials (RentCast)...")
    url = "https://api.rentcast.io/v1/avm/value"
    params = {"address": TEST_ADDRESS, "propertyType": "Single Family"}
    headers = {"accept": "application/json", "X-Api-Key": RENTCAST_KEY}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if response.status_code == 200:
            price = data.get("price", 0)
            rent_min = data.get("rentRange", {}).get("low", 0)
            rent_max = data.get("rentRange", {}).get("high", 0)
            print(f"   ✅ SUCCESS: Financial Data Retrieved")
            print(f"   💰 Est. Value: ${price:,.0f}")
            print(f"   📉 Est. Rent: ${rent_min} - ${rent_max}/mo")
            return True
        else:
            print(f"   ❌ FAILED: {data}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def test_dfw_listing_details():
    print(f"\n🕷️ [2/2] Scraping Zillow Description (Apify)...")
    print("   ⏳ Connecting to Azure & Apify Cloud (takes ~15s)...")
    
    try:
        client = ApifyClient(APIFY_TOKEN)
        
        # Specific input for 'maxcopell/zillow-detail-scraper'
        run_input = {
            "startUrls": [{"url": TEST_ZILLOW_URL}],
            "maxItems": 1
        }

        # Run the actor
        run = client.actor("maxcopell/zillow-detail-scraper").call(run_input=run_input)

        # Fetch results
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        if dataset_items:
            item = dataset_items[0]
            desc = item.get("description", "No description found")
            price = item.get("price", "N/A")
            
            print(f"   ✅ SUCCESS: Listing Scraped")
            print(f"   🏠 Listed Price: ${price}")
            print(f"   📝 Agent Notes: {desc[:100]}...") 
            return True
        else:
            print("   ⚠️  Scraper finished but returned no data.")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("--- 🤠 STARTING DFW MARKET DATA TEST ---")
    fin_status = test_dfw_financials()
    scrape_status = test_dfw_listing_details()
    
    if fin_status and scrape_status:
        print("\n🎉 PHASE 2 COMPLETE: Your DFW Data Pipeline is LIVE.")
    else:
        print("\n⚠️  ISSUES DETECTED. Check error messages above.")