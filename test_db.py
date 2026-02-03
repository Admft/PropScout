import os
import datetime
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, PartitionKey, exceptions

# 1. Load environment variables
load_dotenv()

ENDPOINT = os.getenv("COSMOS_ENDPOINT")
KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "propscout-db"  # We will create/use this specific DB
CONTAINER_NAME = "health_checks"

def run_verification():
    print("🚀 Starting Connectivity Test...")

    if not ENDPOINT or not KEY:
        print("❌ Error: Missing keys in .env file.")
        return

    try:
        # 2. Initialize the Cosmos Client
        client = CosmosClient(ENDPOINT, KEY)
        
        # 3. Create (or get) the Database
        database = client.create_database_if_not_exists(id=DATABASE_NAME)
        print(f"✅ Database '{DATABASE_NAME}' verified.")

        # 4. Create (or get) the Container
        # FIX: Removed 'offer_throughput' because Serverless handles this automatically
        container = database.create_container_if_not_exists(
            id=CONTAINER_NAME, 
            partition_key=PartitionKey(path="/id")
        )
        print(f"✅ Container '{CONTAINER_NAME}' verified.")
        # 5. Insert a Test Document
        test_item = {
            "id": "connection-test-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            "status": "online",
            "message": "Hello from Adam's Laptop!",
            "timestamp": str(datetime.datetime.now())
        }

        container.create_item(body=test_item)
        print("✅ SUCCESS: Test document inserted into Cosmos DB.")
        print("------------------------------------------------")
        print("🎉 Infrastructure Phase 1 Complete. You are ready for the Risk Engine.")

    except exceptions.CosmosHttpResponseError as e:
        print(f"❌ Azure Error: {e.message}")
    except Exception as e:
        print(f"❌ General Error: {e}")

if __name__ == "__main__":
    run_verification()