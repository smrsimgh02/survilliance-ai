from typing import List, Optional
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Session, create_engine, select
import json
import asyncio

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
import os
import cv2
import time
from threading import Lock
import numpy as np



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
    SQLModel.metadata.create_all(engine)



app = FastAPI(
    title="Surveillance AI Hub",
    description="Central backend for managing AI surveillance nodes and data.",
    version="1.0.0"
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

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error broadcasting to WS: {e}")

manager = ConnectionManager()

# Store latest detections for server-side drawing in video stream
latest_detections = {} # {camera_id: [{class, conf, x, y, w, h}, ...]}
latest_detections_lock = Lock()

def get_yolo_color(class_id):
    """Vibrant BGR colors (OpenCV default) for standard YOLO look."""
    colors = [
        (0, 0, 255),   # Red
        (0, 255, 0),   # Green
        (255, 0, 0),   # Blue
        (0, 255, 255), # Yellow
        (255, 0, 255), # Magenta
        (255, 255, 0), # Cyan
        (0, 165, 255), # Orange
        (203, 192, 255), # Pink
        (128, 0, 128), # Purple
        (42, 42, 165), # Brown
    ]
    # Simple hash to keep color consistent for the same class
    return colors[abs(hash(class_id)) % len(colors)]




@app.on_event("startup")
def on_startup():
    print("[BACKEND] Booting up systems...")

# Get path relative to the script location
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/monitor", StaticFiles(directory=static_dir), name="static")



@app.get("/")
async def root():
    return {"message": "Surveillance AI Hub API is running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": str(datetime.datetime.utcnow())}

@app.post("/detections/", status_code=201)
async def create_detection(detection: Detection):
    with Session(engine) as session:
        session.add(detection)
        session.commit()
        session.refresh(detection)
        
        # Update latest detections for server-side drawing while session is active
        with latest_detections_lock:
            # Store a copy of the dict to avoid detached instance issues
            latest_detections[detection.camera_id] = [detection.dict()]
    
    # Broadcast directly
    broadcast_data = detection.dict()
    # Convert datetime to string for JSON serialization
    if "timestamp" in broadcast_data and broadcast_data["timestamp"]:
        broadcast_data["timestamp"] = str(broadcast_data["timestamp"])
    await manager.broadcast(broadcast_data)
    
    return detection

@app.post("/detections/bulk/", status_code=201)
async def create_bulk_detections(detections: List[Detection]):
    # Broadcast FIRST for maximum real-time speed
    broadcast_payload = []
    for d in detections:
        data = d.dict()
        data["timestamp"] = str(datetime.datetime.utcnow())
        broadcast_payload.append(data)
    
    await manager.broadcast(broadcast_payload)
    
    # Then Save to DB
    try:
        with Session(engine) as session:
            for d in detections:
                session.add(d)
            session.commit()
            
            # Cache for server-side drawing
            if detections:
                with latest_detections_lock:
                    latest_detections[detections[0].camera_id] = [d.dict() for d in detections]
    except Exception as e:
        print(f"[ERROR] DB Save failed but broadcast sent: {e}")
        
    return {"status": "success", "count": len(detections)}

@app.get("/detections/", response_model=List[Detection])
async def get_detections(limit: int = 100, camera_id: Optional[str] = None):
    with Session(engine) as session:
        statement = select(Detection).order_by(Detection.timestamp.desc()).limit(limit)
        if camera_id:
            statement = statement.where(Detection.camera_id == camera_id)
        results = session.exec(statement).all()
        return results

@app.get("/cameras/", response_model=List[Camera])
async def get_cameras():
    with Session(engine) as session:
        return session.exec(select(Camera)).all()

@app.post("/cameras/", status_code=201)
async def add_camera(camera: Camera):
    with Session(engine) as session:
        session.add(camera)
        session.commit()
        session.refresh(camera)
        return camera

@app.delete("/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    with Session(engine) as session:
        camera = session.get(Camera, camera_id)
        if not camera:
            return {"error": "Camera not found"}
        session.delete(camera)
        session.commit()
        return {"status": "deleted"}



import threading
local_webcam = None
latest_frame = None
latest_jpeg = None # Shared pre-encoded JPEG bytes
webcam_lock = Lock()

def camera_thread_func():
    global local_webcam, latest_frame, latest_jpeg
    print("[BACKEND] High-Performance Broadcast Thread started.")
    local_webcam = cv2.VideoCapture(0)
    
    while True:
        try:
            success, frame = local_webcam.read()
            if success:
                # 1. Encode ONCE
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    jpeg_bytes = buffer.tobytes()
                    with webcam_lock:
                        latest_frame = frame
                        latest_jpeg = jpeg_bytes
            else:
                print("[BACKEND] Camera Busy/Lost. Recovering...")
                local_webcam.release()
                time.sleep(2)
                local_webcam = cv2.VideoCapture(0)
        except Exception as e:
            print(f"[BACKEND] Camera Thread Error: {e}")
        time.sleep(0.01)

@app.on_event("startup")
def startup_event():
    create_db_and_tables()
    # Run the camera capture in background
    t = threading.Thread(target=camera_thread_func, daemon=True)
    t.start()
    print("[BACKEND] Camera thread active.")

def gen_frames(camera_id: str):
    while True:
        frame_bytes = None
        with webcam_lock:
            frame_bytes = latest_jpeg
        
        if frame_bytes is None:
            # Fallback frame if no signal
            temp_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(temp_frame, "CONNECTING...", (220, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', temp_frame)
            frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.03) # Clean 30fps broadcast

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
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    # Use Dynamic Port for Cluster Simulation
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
