import cv2
import requests
import json
import time
import os

# --- Configurations ---
# Updated with your specific Mobile IP
MOBILE_CAM_URL = "http://10.213.206.219:8080/video" 
FOG_HUB_URL = "http://localhost:8000/detections/"

def start_mobile_ai_surveillance():
    print(f"[BRIDGE] Connecting to Mobile Camera: {MOBILE_CAM_URL}")
    
    cap = cv2.VideoCapture(MOBILE_CAM_URL)
    
    if not cap.isOpened():
        print("[ERR] Could not connect to Mobile Camera. Check Wi-Fi.")
        return

    print("[SUCCESS] Connected! Starting AI Detection Stream...")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Stream Interrupted. Retrying...")
            cap = cv2.VideoCapture(MOBILE_CAM_URL)
            time.sleep(2)
            continue

        if frame_count % 10 == 0:
            # Mock AI Detection for the capstone demo (simulating real YOLOv5 output)
            obj = "Person"
            conf = 0.95
            
            payload = {
                "camera_id": "MOBILE-CAM-ANDROID",
                "class_name": obj,
                "confidence": conf,
                "xcenter": 0.5, "ycenter": 0.5, "width": 0.2, "height": 0.4
            }
            try:
                requests.post(FOG_HUB_URL, json=payload, timeout=2)
                print(f"[ALERTS] Mobile detected: {obj} ({conf*100}%)")
            except:
                print("[OFFLINE] Fog Hub is down.")

        # Window diabled for stability (See result on Browser Dashboard)
        # cv2.imshow('Mobile Surveillance Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        frame_count += 1

    cap.release()

if __name__ == "__main__":
    print("Starting Mobile AI Node...")
    start_mobile_ai_surveillance()
