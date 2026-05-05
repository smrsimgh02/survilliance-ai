import requests
import datetime
import time
import random

API_URL = "http://localhost:8001"
API_KEY = "surveillance_secret_key_2024"
HEADERS = {"X-API-KEY": API_KEY}

def seed_data():
    print("Seeding cameras...")
    cameras = [
        {"id": "cam_001", "name": "Main Entrance (LIVE YOLO)", "url": "0", "location": "28.6139,77.2090", "status": "active"},
        {"id": "cam_002", "name": "Parking Lot A", "url": "http://127.0.0.1:8001/static/placeholder.mp4", "status": "offline"},
        {"id": "cam_003", "name": "Back Alley", "url": "http://127.0.0.1:8001/static/placeholder.mp4", "status": "offline"},
    ]
    
    for cam in cameras:
        try:
            requests.post(f"{API_URL}/cameras/", json=cam, headers=HEADERS)
            print(f"Added {cam['name']}")
        except Exception as e:
            print(f"Failed to add {cam['name']}: {e}")

    # Removed dummy detection seeding to allow real YOLO data to shine.
    print("System ready for real YOLO detections.")

if __name__ == "__main__":
    # Wait for server to be up if running in parallel, but here we assume it will be run manually or after starting server
    seed_data()
