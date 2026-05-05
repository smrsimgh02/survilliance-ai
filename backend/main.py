from typing import List, Optional
import datetime
import os
import time
import logging
import threading
from threading import Lock
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Security, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

import cv2
import models
import database
import manager
import security

Detection = models.Detection
Camera = models.Camera
engine = database.engine
create_db_and_tables = database.create_db_and_tables
manager = manager.manager
verify_api_key = security.verify_api_key
API_KEY = security.API_KEY

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Surveillance-Hub")

app = FastAPI(
    title="Surveillance AI Hub",
    description="Central backend for managing AI surveillance nodes and data.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared State
latest_detections = {} 
latest_detections_lock = Lock()
node_heartbeats = {} # camera_id -> timestamp
heartbeat_lock = Lock()

@app.on_event("startup")
def on_startup():
    logger.info("🚀 Surveillance Hub Booting Up...")
    create_db_and_tables()

# Static files for the dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/monitor", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Dashboard mounted at /monitor")

@app.get("/")
async def root():
    return {"message": "Surveillance AI Hub API is running", "status": "ok", "timestamp": datetime.datetime.utcnow()}

@app.get("/health")
async def health():
    return {"status": "healthy", "uptime": "online", "timestamp": str(datetime.datetime.utcnow())}

@app.websocket("/ws/detections")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Detection Endpoints ---

@app.post("/detections/", status_code=201, dependencies=[Depends(verify_api_key)])
async def create_detection(detection: Detection):
    with heartbeat_lock:
        node_heartbeats[detection.camera_id] = time.time()

    # Convert string timestamp to datetime object for SQLite
    if isinstance(detection.timestamp, str):
        try:
            detection.timestamp = datetime.datetime.fromisoformat(detection.timestamp.replace("Z", "+00:00"))
        except:
            detection.timestamp = datetime.datetime.utcnow()
            
    try:
        with Session(engine) as session:
            session.add(detection)
            session.commit()
            session.refresh(detection)
            with latest_detections_lock:
                latest_detections[detection.camera_id] = [detection.dict()]
    except Exception as e:
        logger.error(f"DB Save failed: {e}")
        
    broadcast_data = detection.dict()
    if "timestamp" in broadcast_data and broadcast_data["timestamp"]:
        broadcast_data["timestamp"] = str(broadcast_data["timestamp"])
    await manager.broadcast(broadcast_data)
    return detection

@app.post("/detections/bulk/", status_code=201, dependencies=[Depends(verify_api_key)])
async def create_bulk_detections(detections: List[Detection]):
    if detections:
        with heartbeat_lock:
            node_heartbeats[detections[0].camera_id] = time.time()

    broadcast_payload = []
    for d in detections:
        # Convert string timestamp to datetime object for SQLite
        if isinstance(d.timestamp, str):
            try:
                d.timestamp = datetime.datetime.fromisoformat(d.timestamp.replace("Z", "+00:00"))
            except:
                d.timestamp = datetime.datetime.utcnow()
        
        data = d.dict()
        data["timestamp"] = str(d.timestamp)
        broadcast_payload.append(data)
    
    await manager.broadcast(broadcast_payload)
    
    try:
        with Session(engine) as session:
            for d in detections:
                session.add(d)
            session.commit()
            if detections:
                with latest_detections_lock:
                    latest_detections[detections[0].camera_id] = [d.dict() for d in detections]
    except Exception as e:
        logger.error(f"DB Bulk Save failed: {e}")
        
    return {"status": "success", "count": len(detections)}

@app.post("/cameras/heartbeat/{camera_id}", dependencies=[Depends(verify_api_key)])
async def node_heartbeat(camera_id: str):
    with heartbeat_lock:
        node_heartbeats[camera_id] = time.time()
    return {"status": "ok"}

@app.get("/detections/", response_model=List[Detection])
async def get_detections(limit: int = 100, camera_id: Optional[str] = None):
    with Session(engine) as session:
        statement = select(Detection).order_by(Detection.timestamp.desc())
        if camera_id:
            statement = statement.where(Detection.camera_id == camera_id)
        statement = statement.limit(limit)
        return session.exec(statement).all()

@app.get("/detections/search", response_model=List[Detection])
async def search_detections(
    camera_id: Optional[str] = None,
    class_name: Optional[str] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    limit: int = 100
):
    with Session(engine) as session:
        statement = select(Detection).order_by(Detection.timestamp.desc())
        
        if camera_id:
            statement = statement.where(Detection.camera_id == camera_id)
        if class_name:
            statement = statement.where(Detection.class_name == class_name)
        if start_date:
            statement = statement.where(Detection.timestamp >= datetime.datetime.combine(start_date, datetime.time.min))
        if end_date:
            statement = statement.where(Detection.timestamp <= datetime.datetime.combine(end_date, datetime.time.max))
            
        statement = statement.limit(limit)
        return session.exec(statement).all()

# --- Camera Manager (Resource Sharing) ---
class CameraManager:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.lock = Lock()
        self.active = False
        self.thread = None

    def start(self):
        with self.lock:
            if not self.active:
                self.active = True
                self.thread = threading.Thread(target=self._update, daemon=True)
                self.thread.start()
                logger.info("Camera Manager: Hardware stream started.")

    def _update(self):
        self.cap = cv2.VideoCapture(0)
        while self.active:
            success, frame = self.cap.read()
            if success:
                with self.lock:
                    self.frame = frame.copy()
            else:
                time.sleep(0.1)
        self.cap.release()

    def get_frame(self):
        with self.lock:
            return self.frame

camera_manager = CameraManager()

@app.on_event("startup")
def on_startup():
    logger.info("🚀 Surveillance Hub Booting Up...")
    create_db_and_tables()
    camera_manager.start()

@app.get("/video_feed/{camera_id}")
async def video_feed(camera_id: str):
    """Shared MJPEG streaming endpoint."""
    def generate():
        while True:
            frame = camera_manager.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.04) # ~25 FPS

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

# --- Camera Endpoints ---
@app.get("/cameras/", response_model=List[Camera])
async def get_cameras():
    with Session(engine) as session:
        cameras = session.exec(select(Camera)).all()
        now = time.time()
        for cam in cameras:
            last_seen = node_heartbeats.get(cam.id, 0)
            if now - last_seen < 30: # 30 second threshold
                cam.status = "active"
            else:
                cam.status = "offline"
        return cameras

@app.post("/cameras/", status_code=201, dependencies=[Depends(verify_api_key)])
async def add_camera(camera: Camera):
    with Session(engine) as session:
        session.add(camera)
        session.commit()
        session.refresh(camera)
        return camera

@app.delete("/cameras/{camera_id}", dependencies=[Depends(verify_api_key)])
async def delete_camera(camera_id: str):
    with Session(engine) as session:
        camera = session.get(Camera, camera_id)
        if not camera:
            return {"error": "Camera not found"}
        session.delete(camera)
        session.commit()
        return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
