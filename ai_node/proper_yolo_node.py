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

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AI-Node")

warnings.filterwarnings("ignore")

# --- Configuration Defaults (Updated via CLI) ---
HUB_URL = "http://localhost:8000"
DETECTIONS_URL = f"{HUB_URL}/detections/"
CAMERAS_URL = f"{HUB_URL}/cameras/"

detection_queue = queue.Queue(maxsize=100) # Background sending queue

def sender_worker():
    """Asynchronous background worker to send detections to hub."""
    while True:
        try:
            payload = detection_queue.get()
            # Always use the current global HUB_URL
            requests.post(f"{HUB_URL}/detections/bulk/", json=payload, timeout=0.5)
            detection_queue.task_done()
        except Exception:
            pass

# Start the background sender
threading.Thread(target=sender_worker, daemon=True).start()

def test_hub():
    try:
        r = requests.get(HUB_URL, timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def get_cameras():
    try:
        r = requests.get(f"{HUB_URL}/cameras/", timeout=3)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

class LatestFrameReader:
    """High-speed thread to always provide the absolute latest frame from a source."""
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Force tiny buffer
        self.latest_frame = None
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(1)
                continue
            with self.lock:
                self.latest_frame = frame

    def get_frame(self):
        with self.lock:
            return self.latest_frame

    def release(self):
        self.running = False
        self.cap.release()

def camera_worker(model, camera):
    """Zero-Latency Inference Worker."""
    cam_id = camera['id']
    cam_url = camera['url']
    cam_name = camera.get('name', cam_id)
    
    logger.info(f"[AI:{cam_name}] Launching High-Speed Pipeline...")
    
    source = f"{HUB_URL}/video_feed/{cam_id}" if cam_url == "0" else cam_url
    reader = LatestFrameReader(source)
    
    try:
        while thread_sentinel.get(cam_id, False):
            frame = reader.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            # YOLO Overdrive Mode: Use 320px for 4x speedup on CPU
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
            
            # REMOVED SLEEP FOR MAX PERFORMANCE
            # time.sleep(0.04) 
            
    except Exception as e:
        logger.error(f"[AI:{cam_name}] Error: {e}")
    finally:
        reader.release()
        logger.info(f"[AI:{cam_name}] Offline.")

camera_threads = {}
thread_sentinel = {}

def run():
    global HUB_URL, DETECTIONS_URL, CAMERAS_URL
    
    parser = argparse.ArgumentParser(description="Surveillance AI Node")
    parser.add_argument("--hub-url", type=str, default="http://localhost:8000", help="URL of the central hub")
    args = parser.parse_args()
    
    HUB_URL = args.hub_url
    DETECTIONS_URL = f"{HUB_URL}/detections/"
    CAMERAS_URL = f"{HUB_URL}/cameras/"

    print("=" * 60)
    print("   SURVEILLANCE AI - INDESTRUCTIBLE REAL-TIME ENGINE")
    print("=" * 60)
    
    # INDESTRUCTIBLE MODE: Wait for Hub
    while not test_hub():
        logger.warning(f"Hub at {HUB_URL} is OFFLINE. Retrying in 5s...")
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
                    t = threading.Thread(target=camera_worker, args=(model, cam_data), daemon=True)
                    t.start()
                    camera_threads[cam_id] = t
                    logger.info(f"[SYSTEM] Dynamic Link established: {cam_id}")

            for cam_id in list(camera_threads.keys()):
                if cam_id not in active_cams:
                    thread_sentinel[cam_id] = False
                    camera_threads.pop(cam_id)
                    logger.info(f"[SYSTEM] Dynamic Link severed: {cam_id}")

        except Exception as e:
            logger.error(f"[SYSTEM] Orchestrator error: {e}")

        time.sleep(5)

if __name__ == "__main__":
    run()
