# 📋 Surveillance AI - Team Tasks

This document tracks who is doing what to avoid overlap and errors.

## 🟢 Person 1: Backend & Core (Folder: `/backend`)
- [ ] Connect the Backend to a real Database (PostgreSQL/SQLite).
- [ ] Create an API endpoint to fetch historical detections.
- [ ] Optimize the WebSocket server for multi-camera support.

## 🔵 Person 2: AI Intelligence (Folder: `/ai_node`)
- [ ] Optimize `proper_yolo_node.py` for better FPS.
- [ ] Add support for Mobile IP Cameras (RTSP streams).
- [ ] Filter out "False Positives" (e.g., only detect 'person' or 'car').

## 🟡 Person 3: Dashboard & UI (Folder: `/dashboard`)
- [ ] Build a React/HTML page to show live bounding boxes.
- [ ] Create a "Search" feature to look for past detections.
- [ ] Add a map view to show where cameras are located.

---
### 🚀 How to work without errors:
1. `git pull origin master` (Start of the day)
2. `git add .` + `git commit -m "added my feature"`
3. `git push origin master` (End of the task)
