# 🔵 Vishal's Task List (AI Intelligence)

Vishal, you are responsible for the AI nodes that process the video feeds.

---

## 🚀 Current Tasks

- [x] **RTSP / IP Camera Support**:
    - *Status: Completed. Added LatestFrameReader with RTSP transport support.*

- [x] **Auth & Security**:
    - *Status: Completed. Node now sends X-API-KEY with every detection.*

- [x] **Class Filtering Logic**:
    - *Status: Completed. Use --classes flag to filter detections.*

- [x] **Multi-Stream Stability**:
    - *Status: Completed. Verified stable performance for 3+ concurrent streams.*

## 🧠 Phase 2: Custom ML Training (Active)
- [ ] **Data Collection**:
    - Download "Weapon Detection" or "Threat" datasets from Roboflow.
- [ ] **Model Training (Colab)**:
    - Train YOLOv5 on custom data and export `best.pt`.
- [x] **Inference Bridge**:
    - Updated `proper_yolo_node.py` to support custom weight loading via `--weights best.pt`.

---

## ✅ Progress Tracking
- 2026-05-06: Implemented RTSP support and security headers. Refactored node to use background threading for network requests.
