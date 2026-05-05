# 🟡 Hemant's Task List (Dashboard & UI)

Welcome Hemant! Your focus is to build a modern, real-time interface for the Surveillance AI system.

---

## 🚀 Current Tasks

- [x] **Initialize Dashboard Project**: 
    - Setup a Vite + React + TypeScript project in the `/dashboard` directory.
    - **Urgent**: Must implement `X-API-KEY` in all fetch/websocket calls.
    - Current `index.html` is failing due to lack of Auth headers.
    - *Status: Completed. Centralized Axios client and WebSocket security layer implemented.*

- [x] **Live Bounding Box Viewer**:
    - Connect to the Backend WebSocket (`ws://172.16.54.102:8000/ws/detections`).
    - Fix alignment issues found in the current prototype (Canvas vs Video aspect ratio).
    - *Status: Completed. Implemented responsive canvas overlay with dynamic scaling.*

---

## 🚩 Frontend GAP Analysis Status

The following issues from the legacy prototype have been resolved in the new React dashboard:
1. ✅ **API Key Support**: Mandatory `X-API-KEY` header added to all communications.
2. ✅ **Dynamic URLs**: Camera feeds and node data are fetched dynamically from the API.
3. ✅ **Error Handling**: Added state-based loading and error indicators.
4. ✅ **Performance**: Replaced CPU-heavy loops with high-performance Canvas rendering.

---

## 🏗️ Remaining Tasks

- [ ] **Detection History Search**:
    - Create a UI to fetch and filter past detections from the Hub's API.
    - *Note: Samar needs to provide the `/detections/search` endpoint first.*

- [ ] **Camera Map View**:
    - Use Leaflet to show camera locations on a map.
    - Integrate GPS coordinates from the node metadata.

---

## 🛠️ Setup Instructions for Hemant

1. **Get the Code**:
   ```bash
   git pull origin master
   ```
2. **Run the Dashboard**:
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```
3. **Hub IP**: 
   The central backend is at `172.16.54.102:8000`.

---

## ✅ Progress Tracking
*Update this file whenever you finish a task!*

- 2026-05-06: Initialized React dashboard, implemented security headers, and fixed real-time YOLO visualization.
