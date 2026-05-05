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
        {"id": "cam_001", "name": "Main Entrance", "url": "0", "location": "28.6139,77.2090", "status": "active"},
        {"id": "cam_002", "name": "Parking Lot A", "url": "0", "location": "28.6150,77.2100", "status": "active"},
        {"id": "cam_003", "name": "Back Alley", "url": "0", "location": "28.6120,77.2080", "status": "active"},
    ]
    
    for cam in cameras:
        try:
            requests.post(f"{API_URL}/cameras/", json=cam, headers=HEADERS)
            print(f"Added {cam['name']}")
        except Exception as e:
            print(f"Failed to add {cam['name']}: {e}")

    print("Seeding detections...")
    classes = ["person", "car", "dog", "bicycle"]
    for i in range(20):
        cam = random.choice(cameras)
        detection = {
            "camera_id": cam["id"],
            "class_name": random.choice(classes),
            "confidence": random.uniform(0.7, 0.99),
            "xcenter": random.uniform(0.1, 0.9),
            "ycenter": random.uniform(0.1, 0.9),
            "width": random.uniform(0.05, 0.2),
            "height": random.uniform(0.1, 0.3),
            "timestamp": (datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(0, 1000))).isoformat()
        }
        try:
            requests.post(f"{API_URL}/detections/", json=detection, headers=HEADERS)
        except Exception as e:
            print(f"Failed to add detection: {e}")

if __name__ == "__main__":
    # Wait for server to be up if running in parallel, but here we assume it will be run manually or after starting server
    seed_data()
