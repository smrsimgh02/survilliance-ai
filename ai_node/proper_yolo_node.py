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
<<<<<<< HEAD

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
=======
import os
from dotenv import load_dotenv

# Load Configuration
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde
)
logger = logging.getLogger("AI-Node")

warnings.filterwarnings("ignore")

<<<<<<< HEAD
# --- Configuration Defaults (Updated via CLI) ---
HUB_URL = "http://localhost:8000"
=======
# --- Configuration ---
parser = argparse.ArgumentParser(description="Surveillance AI Node")
parser.add_argument("--hub-url", default=os.getenv("HUB_URL", "http://localhost:8000"), help="URL of the Central Hub")
args = parser.parse_args()

HUB_URL = args.hub_url
API_KEY = os.getenv("API_KEY", "surveillance_secret_key_2024")
HEADERS = {"X-API-KEY": API_KEY}

>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde
DETECTIONS_URL = f"{HUB_URL}/detections/"
CAMERAS_URL = f"{HUB_URL}/cameras/"

detection_queue = queue.Queue(maxsize=100) # Background sending queue

def sender_worker():
    """Asynchronous background worker to send detections to hub."""
    while True:
        try:
            payload = detection_queue.get()
<<<<<<< HEAD
            # Always use the current global HUB_URL
            requests.post(f"{HUB_URL}/detections/bulk/", json=payload, timeout=0.5)
            detection_queue.task_done()
        except Exception:
            pass
=======
            response = requests.post(f"{HUB_URL}/detections/bulk/", json=payload, headers=HEADERS, timeout=1.0)
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
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde

# Start the background sender
threading.Thread(target=sender_worker, daemon=True).start()

def test_hub():
    """Check if the hub is reachable."""
    try:
        r = requests.get(HUB_URL, headers=HEADERS, timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def get_cameras():
    """Fetch camera configuration from hub."""
    try:
<<<<<<< HEAD
        r = requests.get(f"{HUB_URL}/cameras/", timeout=3)
=======
        r = requests.get(CAMERAS_URL, headers=HEADERS, timeout=3)
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

class LatestFrameReader:
    """High-speed thread to always provide the absolute latest frame from a source."""
    def __init__(self, source):
        self.source = source
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
        self.latest_frame = None
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning(f"Lost connection to stream: {self.source}. Retrying...")
                self.cap.release()
                time.sleep(2)
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

def camera_worker(model, camera, thread_sentinel):
    """Zero-Latency Inference Worker."""
    cam_id = camera['id']
    cam_url = camera['url']
    cam_name = camera.get('name', cam_id)
    
<<<<<<< HEAD
    logger.info(f"[AI:{cam_name}] Launching High-Speed Pipeline...")
=======
    logger.info(f"Launching AI Pipeline for {cam_name}...")
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde
    
    source = f"{HUB_URL}/video_feed/{cam_id}" if cam_url == "0" else cam_url
    reader = LatestFrameReader(source)
    
    try:
        while thread_sentinel.get(cam_id, False):
            frame = reader.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            # YOLO Optimized Inference
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = model(img, size=320) 
            dets = results.pandas().xyxy[0]
            h, w, _ = frame.shape

            if not dets.empty:
                payloads = []
                for _, d in dets.iterrows():
                    payloads.append({
                        "camera_id": cam_id,
                        "class_name": d['name'],
                        "confidence": float(d['confidence']),
                        "xcenter": float((d['xmin'] + d['xmax']) / 2 / w),
                        "ycenter": float((d['ymin'] + d['ymax']) / 2 / h),
                        "width": float((d['xmax'] - d['xmin']) / w),
                        "height": float((d['ymax'] - d['ymin']) / h)
                    })
                
                if detection_queue.full():
                    try: detection_queue.get_nowait()
                    except: pass
                detection_queue.put(payloads)
            
    except Exception as e:
<<<<<<< HEAD
        logger.error(f"[AI:{cam_name}] Error: {e}")
    finally:
        reader.release()
        logger.info(f"[AI:{cam_name}] Offline.")

camera_threads = {}
thread_sentinel = {}
=======
        logger.error(f"AI Worker [{cam_name}] Error: {e}")
    finally:
        reader.release()
        logger.info(f"AI Worker [{cam_name}] Offline.")
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde

def run():
    global HUB_URL, DETECTIONS_URL, CAMERAS_URL
    
    parser = argparse.ArgumentParser(description="Surveillance AI Node")
    parser.add_argument("--hub-url", type=str, default="http://localhost:8000", help="URL of the central hub")
    args = parser.parse_args()
    
    HUB_URL = args.hub_url
    DETECTIONS_URL = f"{HUB_URL}/detections/"
    CAMERAS_URL = f"{HUB_URL}/cameras/"

    print("=" * 60)
<<<<<<< HEAD
    print("   SURVEILLANCE AI - INDESTRUCTIBLE REAL-TIME ENGINE")
    print("=" * 60)
    
    # INDESTRUCTIBLE MODE: Wait for Hub
    while not test_hub():
        logger.warning(f"Hub at {HUB_URL} is OFFLINE. Retrying in 5s...")
        time.sleep(5)

    logger.info("Hub Connection Verified. Loading Neural Core...")
=======
    print("   SURVEILLANCE AI - PRODUCTION READY ENGINE")
    print(f"   Connecting to Hub at: {HUB_URL}")
    print("=" * 60)
    
    # Auto-Reconnect Loop for the Hub
    while not test_hub():
        logger.error("Hub Offline. Retrying in 5 seconds...")
        time.sleep(5)

    logger.info("Hub Online! Loading Neural Core...")
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    try:
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(device)
        model.conf = 0.25
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return
    
    if device == 'cpu':
        torch.set_num_threads(4) 
    
<<<<<<< HEAD
    logger.info(f"Core Engine: ONLINE using {device} (320px Optimized)\n")
=======
    logger.info(f"Core Engine: ONLINE using {device}")

    camera_threads = {}
    thread_sentinel = {}
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde

    while True:
        try:
            cameras = get_cameras()
            if not cameras and not test_hub():
<<<<<<< HEAD
                logger.warning("Lost connection to Hub. Attempting to reconnect...")
                while not test_hub():
                    time.sleep(5)
                logger.info("Reconnected to Hub.")
=======
                logger.warning("Lost connection to Hub. Searching...")
                time.sleep(5)
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde
                continue

            active_cams = {c['id']: c for c in cameras if c.get('status') == 'active'}
            
            # Start new threads
            for cam_id, cam_data in active_cams.items():
                if cam_id not in camera_threads or not camera_threads[cam_id].is_alive():
                    thread_sentinel[cam_id] = True
                    t = threading.Thread(target=camera_worker, args=(model, cam_data, thread_sentinel), daemon=True)
                    t.start()
                    camera_threads[cam_id] = t
<<<<<<< HEAD
                    logger.info(f"[SYSTEM] Dynamic Link established: {cam_id}")
=======
                    logger.info(f"Started Monitoring: {cam_id}")
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde

            # Clean up dead threads
            for cam_id in list(camera_threads.keys()):
                if cam_id not in active_cams:
                    logger.info(f"Stopping Monitoring: {cam_id}")
                    thread_sentinel[cam_id] = False
                    camera_threads.pop(cam_id)
                    logger.info(f"[SYSTEM] Dynamic Link severed: {cam_id}")

        except Exception as e:
<<<<<<< HEAD
            logger.error(f"[SYSTEM] Orchestrator error: {e}")
=======
            logger.error(f"Orchestrator error: {e}")
>>>>>>> 37b9bdb04e172dfa9635cf4a8d6f6069bf4f8dde

        time.sleep(5)

if __name__ == "__main__":
    run()

