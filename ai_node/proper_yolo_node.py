import cv2
import torch
import requests
import time
import sys
import warnings
import threading
import queue
import datetime
import argparse
import logging
import os
from dotenv import load_dotenv

# Load Configuration from .env
load_dotenv()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("AI-Node")

warnings.filterwarnings("ignore")

# --- Configuration & Auth ---
# These can be set via .env or CLI
API_KEY = os.getenv("API_KEY", "surveillance_secret_key_2024")
HEADERS = {"X-API-KEY": API_KEY}

# CLI Arguments take precedence
parser = argparse.ArgumentParser(description="Surveillance AI Node")
parser.add_argument("--hub-url", type=str, default=os.getenv("HUB_URL", "http://localhost:8001"), help="URL of the central hub")
parser.add_argument("--classes", nargs='+', default=None, help="Filter classes (e.g. --classes person car)")
args, unknown = parser.parse_known_args() 

HUB_URL = args.hub_url
FILTER_CLASSES = args.classes
DETECTIONS_URL = f"{HUB_URL}/detections/"
CAMERAS_URL = f"{HUB_URL}/cameras/"

detection_queue = queue.Queue(maxsize=100) # Background sending queue

def sender_worker():
    """Asynchronous background worker to send detections to hub with Auth."""
    while True:
        try:
            payload = detection_queue.get()
            # Always use the current global HUB_URL and HEADERS
            response = requests.post(f"{HUB_URL}/detections/bulk/", json=payload, headers=HEADERS, timeout=1.5)
            if response.status_code == 201:
                detection_queue.task_done()
            else:
                logger.warning(f"Failed to send detections: Status {response.status_code}")
        except requests.exceptions.RequestException:
            # Silently wait if hub is down, don't crash
            time.sleep(1)
        except Exception as e:
            logger.error(f"Sender Error: {e}")
            time.sleep(1)

# Start the background sender
threading.Thread(target=sender_worker, daemon=True).start()

def heartbeat_worker():
    """Periodic heartbeat to keep camera status 'Online' on the dashboard."""
    while True:
        try:
            # Send heartbeat for all active cameras this node might be handling
            # In a real setup, this would be camera-specific.
            # Here we just fetch cameras and ping the ones we see.
            r = requests.get(f"{HUB_URL}/cameras/", headers=HEADERS, timeout=1)
            if r.status_code == 200:
                for cam in r.json():
                    if cam.get('status') == 'active':
                        requests.post(f"{HUB_URL}/cameras/heartbeat/{cam['id']}", headers=HEADERS, timeout=1)
        except:
            pass
        time.sleep(10)

threading.Thread(target=heartbeat_worker, daemon=True).start()

def test_hub():
    """Check if the hub is reachable and authorized."""
    try:
        r = requests.get(HUB_URL, headers=HEADERS, timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def get_cameras():
    """Fetch camera configuration from hub."""
    try:
        r = requests.get(CAMERAS_URL, headers=HEADERS, timeout=3)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

class LatestFrameReader:
    """High-speed thread to always provide the absolute latest frame from a source (Supports RTSP)."""
    def __init__(self, source):
        self.source = source
        self.cap = cv2.VideoCapture(source)
        
        # RTSP Specific Optimizations
        if "rtsp" in source.lower():
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            # Use TCP for better stability in some networks
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
            
        self.latest_frame = None
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning(f"Stream connection lost: {self.source}. Attempting recovery...")
                self.cap.release()
                time.sleep(3)
                self.cap = cv2.VideoCapture(self.source)
                continue
            with self.lock:
                self.latest_frame = frame

    def get_frame(self):
        with self.lock:
            return self.latest_frame

    def release(self):
        self.running = False
        self.cap.release()

def camera_worker(model, camera, sentinel):
    """Zero-Latency Inference Worker with Class Filtering."""
    cam_id = camera['id']
    cam_url = camera['url']
    cam_name = camera.get('name', cam_id)
    
    logger.info(f"Launching AI Pipeline for {cam_name}...")
    
    source = f"{HUB_URL}/video_feed/{cam_id}" if cam_url == "0" else cam_url
    reader = LatestFrameReader(source)
    
    try:
        while sentinel.get(cam_id, False):
            frame = reader.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            # YOLO Overdrive Mode: Use 320px for 4x speedup on CPU
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = model(img, size=320) 
            dets = results.pandas().xyxy[0]
            h, w, _ = frame.shape

            if not dets.empty:
                payloads = []
                for _, d in dets.iterrows():
                    # Apply Class Filtering (Vishal's Task)
                    if FILTER_CLASSES and d['name'].lower() not in [c.lower() for c in FILTER_CLASSES]:
                        continue

                    payloads.append({
                        "camera_id": cam_id,
                        "class_name": d['name'],
                        "confidence": float(d['confidence']),
                        "xcenter": float((d['xmin'] + d['xmax']) / 2 / w),
                        "ycenter": float((d['ymin'] + d['ymax']) / 2 / h),
                        "width": float((d['xmax'] - d['xmin']) / w),
                        "height": float((d['ymax'] - d['ymin']) / h)
                    })
                
                if payloads:
                    if detection_queue.full():
                        try: detection_queue.get_nowait()
                        except: pass
                    detection_queue.put(payloads)
            
    except Exception as e:
        logger.error(f"AI Worker [{cam_name}] Error: {e}")
    finally:
        reader.release()
        logger.info(f"AI Worker [{cam_name}] Offline.")

def run():
    print("=" * 60)
    print("   SURVEILLANCE AI - INDESTRUCTIBLE PRODUCTION ENGINE")
    print(f"   Target Hub: {HUB_URL}")
    print("=" * 60)
    
    # INDESTRUCTIBLE MODE: Wait for Hub
    while not test_hub():
        logger.warning(f"Hub at {HUB_URL} is OFFLINE or UNAUTHORIZED. Retrying in 5s...")
        time.sleep(5)

    logger.info("Hub Connection Verified. Loading Neural Core...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    try:
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(device)
        model.conf = 0.25
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return
    
    # Maximize CPU usage for low-latency
    if device == 'cpu':
        torch.set_num_threads(4) 
    
    logger.info(f"Core Engine: ONLINE using {device} (320px Optimized)\n")

    camera_threads = {}
    thread_sentinel = {}

    while True:
        try:
            cameras = get_cameras()
            if not cameras and not test_hub():
                logger.warning("Lost connection to Hub. Attempting to reconnect...")
                while not test_hub():
                    time.sleep(5)
                logger.info("Reconnected to Hub.")
                continue

            active_cams = {c['id']: c for c in cameras if c.get('status') == 'active'}
            
            for cam_id, cam_data in active_cams.items():
                if cam_id not in camera_threads or not camera_threads[cam_id].is_alive():
                    thread_sentinel[cam_id] = True
                    t = threading.Thread(target=camera_worker, args=(model, cam_data, thread_sentinel), daemon=True)
                    t.start()
                    camera_threads[cam_id] = t
                    logger.info(f"Started Monitoring: {cam_id}")

            for cam_id in list(camera_threads.keys()):
                if cam_id not in active_cams:
                    thread_sentinel[cam_id] = False
                    camera_threads.pop(cam_id)
                    logger.info(f"Stopped Monitoring: {cam_id}")

        except Exception as e:
            logger.error(f"Orchestrator error: {e}")

        time.sleep(5)

if __name__ == "__main__":
    run()
