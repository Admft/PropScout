import os
import requests
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load secrets
load_dotenv()
RENTCAST_KEY = os.getenv("RENTCAST_API_KEY")
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
TEST_ADDRESS = "1200 Woodbridge Pkwy, Wylie, TX 75098"
TEST_ZILLOW_URL = "https://www.zillow.com/homedetails/1200-Woodbridge-Pkwy-Wylie-TX-75098/26936553_zpid/"

def test_rentcast():
    print(f"\n📡 [1/2] Connecting to RentCast (Financials)...")
    url = "https://api.rentcast.io/v1/avm/value"
    params = {"address": TEST_ADDRESS, "propertyType": "Single Family"}
    headers = {"accept": "application/json", "X-Api-Key": RENTCAST_KEY}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if response.status_code == 200:
            price = data.get("price", 0)
            print(f"   ✅ SUCCESS: RentCast Data Received")
            print(f"   💰 Est. Price: ${price:,}")
            return True
        else:
            print(f"   ❌ FAILED: {data}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def test_apify():
    print(f"\n🕷️ [2/2] Connecting to Apify (Zillow Detail Scraper by maxcopell)...")
    print("   ⏳ This may take 15-30 seconds...")
    
    try:
        client = ApifyClient(APIFY_TOKEN)
        
        # Input for maxcopell/zillow-detail-scraper
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
            # Try to grab the description (fields vary slightly by scraper)
            desc = item.get("description", "No description found")
            price = item.get("price", "N/A")
            
            print(f"   ✅ SUCCESS: Apify Scrape Complete")
            print(f"   🏠 Zillow Price: ${price}")
            print(f"   📝 Description Snippet: {desc[:100]}...") 
            return True
        else:
            print("   ⚠️  Scraper finished but returned no data.")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("--- 🚀 STARTING CORPORATE DATA TEST ---")
    rc_status = test_rentcast()
    ap_status = test_apify()
    
    if rc_status and ap_status:
        print("\n🎉 PHASE 2 COMPLETE: Data Pipelines are ACTIVE.")
    else:
        print("\n⚠️  ISSUES DETECTED. Check error messages above.")