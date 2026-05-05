import requests
import time
import os
import json

# Local Fog Hub Configuration
FOG_DB_URL = "http://localhost:8000/detections/?limit=1000"

# Remote Cloud Configuration (Dummy Endpoint)
CLOUD_ARCHIVE_URL = os.getenv("CLOUD_UPSTREAM_URL", "https://api.cloud-analytics.com/upload")

def sync_fog_to_cloud():
    print("[FOG-TO-CLOUD] Sync: Polling for local detections...")
    try:
        # 1. Fetch latest data from our Fog Hub (K8s Service)
        response = requests.get(FOG_DB_URL)
        if response.status_code == 200:
            local_data = response.json()
            if not local_data:
                print("[SYNC] Everything is up to date.")
                return

            # 2. Package and Push to Cloud
            print(f"[PACKAGING] {len(local_data)} activities for Global Archive...")
            sync_payload = {
                "site_id": os.getenv("SITE_ID", "MUMBAI-01"),
                "data": local_data
            }
            
            # (Simulation: Only printing to avoid real connection error)
            print(f"[SUCCESS] Handed over {len(local_data)} records to Global Data Lake.")
            
        else:
            print(f"[FAIL] Local Hub unreachable. Status: {response.status_code}")
    except Exception as e:
        print(f"[ERR] Sync error: {e}")

if __name__ == "__main__":
    while True:
        sync_fog_to_cloud()
        time.sleep(3600) # Sync every hour
