import threading
import requests
import time
import random
import sys

BACKEND_URL = "http://localhost:8000/detections/"

def camera_worker(camera_id):
    objects = ["Person", "Vehicle", "Backpack", "Gun (Mock)", "Dog"]
    for i in range(5):
        obj = random.choice(objects)
        conf = round(random.uniform(0.7, 0.99), 2)
        payload = {
            "camera_id": camera_id,
            "class_name": obj,
            "confidence": conf,
            "xcenter": 0.5,
            "ycenter": 0.5,
            "width": 0.2,
            "height": 0.4
        }
        try:
            resp = requests.post(BACKEND_URL, json=payload, timeout=2)
            if resp.status_code == 201:
                print(f"[OK] {camera_id}: Detected {obj} ({conf*100}%)")
            else:
                print(f"[FAIL] {camera_id}: Code {resp.status_code}")
        except Exception as e:
            print(f"[ERR] {camera_id}: {e}")
        time.sleep(1)

def run_simulation():
    print("Starting Simulation of 5 Cameras...")
    threads = []
    for i in range(5):
        cam_id = f"CAM-NODE-{i+1}"
        t = threading.Thread(target=camera_worker, args=(cam_id,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    print("\nSimulation Complete. Verifying Database Status...")
    try:
        count_resp = requests.get(BACKEND_URL)
        detections = count_resp.json()
        print(f"Total detections in database: {len(detections)}")
        print(f"Latest 3 entries: {[d['class_name'] for d in detections[:3]]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_simulation()
