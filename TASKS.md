# 📋 Surveillance AI - Team Tasks

## 🟢 Person 1 (Samar): Backend & Core (Folder: `/backend`)
- [x] Initialized Git and Production Plan.
- [x] Connect the Backend to a real Database (SQLite/PostgreSQL).
- [ ] Create an API endpoint to fetch historical detections.
- [ ] Optimize the WebSocket server for multi-camera support.
- [x] Implement API Key Security (`X-API-KEY`).

## 🔵 Person 2 (Hemant): AI Intelligence (Folder: `/ai_node`)
- [x] Optimized with Auto-Reconnect logic for better FPS.
- [ ] Add support for Mobile IP Cameras (RTSP streams).
- [ ] Filter out "False Positives" (e.g., only detect 'person' or 'car').

## 🟡 Person 3 (Vishal): Dashboard & UI (Folder: `/dashboard`)
- [x] Build a Modern Web Dashboard to see live bounding boxes.
- [ ] Create a "Search" feature to look for past detections.
- [ ] Add a map view to show where cameras are located.
- [x] Dockerize the entire stack for easy sync.

---
### 🚀 Sync Commands:
1. `git pull origin master` (To get teammates' work)
2. `git add .`
3. `git commit -m "Your Message"`
4. `git push origin master` (To share your work)
