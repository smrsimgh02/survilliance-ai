# 🔵 Vishal's Task List (AI Intelligence)

Vishal, you are responsible for the AI nodes that process the video feeds.

---

## 🚀 Current Tasks

- [x] **RTSP / IP Camera Support**: [VERIFIED ✅]
    - Updated `proper_yolo_node.py` to support RTSP streams with TCP transport and auto-recovery.
- [x] **Class Filtering**: [VERIFIED ✅]
    - Added `--classes` CLI argument to filter detections (e.g., `python proper_yolo_node.py --classes person car`).
- [ ] **FPS Optimization**:
    - Test the node on different hardware and optimize the inference size (currently 320px).
- [x] **Maintenance**: [VERIFIED ✅]
    - "Indestructible" mode (auto-reconnect) is fully integrated with Samar's API Security system.

---

## 🛠️ Tech Note (Production Gap)
The `proper_yolo_node.py` now supports `.env` and `API_KEY`. Make sure to keep your local `.env` updated with the Hub's credentials.

---

## ✅ Progress Tracking
*Update this file whenever you finish a task!*
