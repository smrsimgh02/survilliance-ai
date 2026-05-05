from typing import List, Optional
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Session, create_engine, select
import json
import asyncio
import logging
from dotenv import load_dotenv

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
import os
import cv2
import time
from threading import Lock
import numpy as np

# --- Setup Configuration ---
load_dotenv()
API_KEY = os.getenv("API_KEY", "surveillance_secret_key_2024")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Surveillance-Hub")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=403,
        detail="Unauthorized node: Invalid API Key."
    )

class Detection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    camera_id: str
    class_name: str
    confidence: float
    xcenter: float
    ycenter: float
    width: float
    height: float
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class Camera(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    url: str
    location: Optional[str] = None
    status: str = "active"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    logger.info("Initializing database...")
    SQLModel.metadata.create_all(engine)

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

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Broadcast failed for a client: {e}")

manager = ConnectionManager()

# Store latest detections for server-side drawing
latest_detections = {} 
latest_detections_lock = Lock()

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

@app.post("/detections/", status_code=201, dependencies=[Depends(verify_api_key)])
async def create_detection(detection: Detection):
    try:
        with Session(engine) as session:
            session.add(detection)
            session.commit()
            session.refresh(detection)
            with latest_detections_lock:
                latest_detections[detection.camera_id] = [detection.dict()]
    except Exception as e:
        logger.error(f"Error saving detection: {e}")
        return {"error": str(e)}
    
    broadcast_data = detection.dict()
    if "timestamp" in broadcast_data and broadcast_data["timestamp"]:
        broadcast_data["timestamp"] = str(broadcast_data["timestamp"])
    await manager.broadcast(broadcast_data)
    return detection

@app.post("/detections/bulk/", status_code=201, dependencies=[Depends(verify_api_key)])
async def create_bulk_detections(detections: List[Detection]):
    broadcast_payload = []
    for d in detections:
        data = d.dict()
        data["timestamp"] = str(datetime.datetime.utcnow())
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

# --- Camera Endpoints ---
@app.get("/cameras/", response_model=List[Camera])
async def get_cameras():
    with Session(engine) as session:
        return session.exec(select(Camera)).all()

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
        return {"status": "deleted"}

# --- Video Streaming Logic ---
local_webcam = None
latest_frame = None
latest_jpeg = None 
webcam_lock = Lock()

def camera_thread_func():
    global local_webcam, latest_frame, latest_jpeg
    local_webcam = cv2.VideoCapture(0)
    while True:
        try:
            success, frame = local_webcam.read()
            if success:
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    jpeg_bytes = buffer.tobytes()
                    with webcam_lock:
                        latest_frame = frame
                        latest_jpeg = jpeg_bytes
            else:
                local_webcam.release()
                time.sleep(2)
                local_webcam = cv2.VideoCapture(0)
        except Exception as e:
            logger.error(f"Camera Thread Error: {e}")
        time.sleep(0.01)

def gen_frames(camera_id: str):
    while True:
        frame_bytes = None
        with webcam_lock:
            frame_bytes = latest_jpeg
        
        if frame_bytes is None:
            temp_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(temp_frame, "CONNECTING...", (220, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', temp_frame)
            frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)

@app.get("/video_feed/{camera_id}")
async def video_feed(camera_id: str):
    with Session(engine) as session:
        camera = session.get(Camera, camera_id)
        if camera and camera.url == "0":
            return StreamingResponse(gen_frames(camera_id), media_type='multipart/x-mixed-replace; boundary=frame')
        return {"error": "Use direct URL for IP cams or camera not found"}

@app.websocket("/ws/detections")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
