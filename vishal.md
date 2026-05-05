# 🔵 Vishal's Task List (AI Intelligence)

Vishal, you are responsible for the AI nodes that process the video feeds.

---

## 🚀 Current Tasks

- [x] **RTSP / IP Camera Support**:
    - *Status: Completed. Added LatestFrameReader with RTSP transport support.*

- [x] **Auth & Security**:
    - *Status: Completed. Node now sends X-API-KEY with every detection.*

- [ ] **Class Filtering Logic (Next)**:
    - **Task**: Use the `--classes` CLI flag to drop unwanted detections before they are sent to the hub.
    - **Goal**: Save bandwidth by only sending critical detections (e.g., 'person').

- [ ] **Multi-Stream Stability**:
    - Test running 3+ cameras on a single node and monitor FPS.

---

## ✅ Progress Tracking
- 2026-05-06: Implemented RTSP support and security headers. Refactored node to use background threading for network requests.
