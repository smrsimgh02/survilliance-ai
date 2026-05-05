# Surveillance AI System

A distributed surveillance system with AI-powered object detection, central data aggregation, and a real-time dashboard.

## 🏗️ Architecture

- **Backend Hub (`/backend`)**: A FastAPI-based central server that manages camera metadata, stores detection history in SQLite, and provides real-time updates via WebSockets.
- **AI Node (`/ai_node`)**: Edge nodes running YOLOv5 for object detection. These nodes process local camera feeds and send results to the central hub.
- **Dashboard (`/dashboard`)**: (Coming Soon) A modern web interface to visualize detections and camera status.
- **Kubernetes (`/k8s`)**: Deployment configurations for scaling the system.

## 🚀 Getting Started

### 1. Start the Central Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```
The server will be available at `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.

### 2. Configure AI Nodes
The AI nodes in `ai_node/` should be configured to send detection payloads to the backend's `/detections/` endpoint.

## 🛠️ Features
- **Real-time WebSockets**: Push detections instantly to connected dashboards.
- **Persistent Storage**: SQLite database for historical detection logs.
- **Scalable Design**: Prepared for Kubernetes deployment.
- **Interactive API Docs**: Fully documented REST API with Swagger.
