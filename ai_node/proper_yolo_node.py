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

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("AI-Node")

warnings.filterwarnings("ignore")

# --- Argument Parsing ---
parser = argparse.ArgumentParser(description="Surveillance AI Node")
parser.add_argument("--hub-url", default="http://localhost:8000", help="URL of the Central Hub")
args = parser.parse_args()

HUB_URL = args.hub_url
DETECTIONS_URL = f"{HUB_URL}/detections/"
CAMERAS_URL = f"{HUB_URL}/cameras/"

detection_queue = queue.Queue(maxsize=100) # Background sending queue

def sender_worker():
    """Asynchronous background worker to send detections to hub."""
    while True:
        try:
            payload = detection_queue.get()
            response = requests.post(f"{HUB_URL}/detections/bulk/", json=payload, timeout=1.0)
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

def test_hub():
    """Check if the hub is reachable."""
    try:
        r = requests.get(HUB_URL, timeout=3)
        return r.status_code == 200
    except:
        return False

def get_cameras():
    """Fetch camera configuration from hub."""
    try:
        r = requests.get(CAMERAS_URL, timeout=3)
        return r.json() if r.status_code == 200 else []
    except:
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
    
    logger.info(f"Launching AI Pipeline for {cam_name}...")
    
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
        logger.error(f"AI Worker [{cam_name}] Error: {e}")
    finally:
        reader.release()
        logger.info(f"AI Worker [{cam_name}] Offline.")

def run():
    print("=" * 60)
    print("   SURVEILLANCE AI - PRODUCTION READY ENGINE")
    print(f"   Connecting to Hub at: {HUB_URL}")
    print("=" * 60)
    
    # Auto-Reconnect Loop for the Hub
    while not test_hub():
        logger.error("Hub Offline. Retrying in 5 seconds...")
        time.sleep(5)

    logger.info("Hub Online! Loading Neural Core...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(device)
    model.conf = 0.25
    
    if device == 'cpu':
        torch.set_num_threads(4) 
    
    logger.info(f"Core Engine: ONLINE using {device}")

    camera_threads = {}
    thread_sentinel = {}

    while True:
        try:
            cameras = get_cameras()
            if not cameras and not test_hub():
                logger.warning("Lost connection to Hub. Searching...")
                time.sleep(5)
                continue

            active_cams = {c['id']: c for c in cameras if c.get('status') == 'active'}
            
            # Start new threads
            for cam_id, cam_data in active_cams.items():
                if cam_id not in camera_threads or not camera_threads[cam_id].is_alive():
                    thread_sentinel[cam_id] = True
                    t = threading.Thread(target=camera_worker, args=(model, cam_data, thread_sentinel), daemon=True)
                    t.start()
                    camera_threads[cam_id] = t
                    logger.info(f"Started Monitoring: {cam_id}")

            # Clean up dead threads
            for cam_id in list(camera_threads.keys()):
                if cam_id not in active_cams:
                    logger.info(f"Stopping Monitoring: {cam_id}")
                    thread_sentinel[cam_id] = False
                    camera_threads.pop(cam_id)

        except Exception as e:
            logger.error(f"Orchestrator error: {e}")

        time.sleep(5)

if __name__ == "__main__":
    run()

