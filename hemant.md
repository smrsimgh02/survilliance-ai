# 🟡 Hemant's Task List (Dashboard & UI)

Welcome Hemant! Your focus is to build a modern, real-time interface for the Surveillance AI system.

---

## 🚀 Current Tasks

- [ ] **Initialize Dashboard Project**: 
    - Setup a Vite + React + TypeScript project in the `/dashboard` directory.
    - **Urgent**: Must implement `X-API-KEY` in all fetch/websocket calls.
    - Current `index.html` is failing due to lack of Auth headers.

- [ ] **Live Bounding Box Viewer**:
    - Connect to the Backend WebSocket (`ws://172.16.54.102:8000/ws/detections`).
    - Fix alignment issues found in the current prototype (Canvas vs Video aspect ratio).

---

## 🚩 Frontend GAP Analysis (For Hemant)
The current `index.html` prototype has the following issues that you must fix in the React version:
1. **No API Key Support**: The backend now requires an API key, but the UI isn't sending it.
2. **Hardcoded URLs**: Don't hardcode camera URLs; fetch them dynamically from the API.
3. **No Error Handling**: The prototype crashes silently if the network fails. Use Error Boundaries and Try/Catch.
4. **Performance**: Use a `ResizeObserver` for the canvas instead of `setInterval`.

- [ ] **Detection History Search**:
    - Create a UI to fetch and filter past detections from the Hub's API.

- [ ] **Camera Map View**:
    - Use Leaflet to show camera locations on a map.

---

## 🛠️ Setup Instructions for Hemant

1. **Get the Code**:
   ```bash
   git pull origin master
   ```
2. **Read the Guide**:
   Check `collaboration_setup_guide.md` for team rules.
3. **Hub IP**: 
   The central backend is at `172.16.54.102:8000`.

---

## ✅ Progress Tracking
*Update this file whenever you finish a task!*
