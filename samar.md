# 🔴 Samar's Task List (Backend & Core)

Samar, you are responsible for the heart of the system—the Central Hub.

---

## 🚀 Current Tasks

- [x] **Backend Modularization**: 
    - Split `main.py` into `models.py`, `database.py`, `manager.py`, and `security.py`.
    - *Status: Completed. Backend is now scalable.*

- [x] **Security Enforcement**:
    - Implement a consistent `X-API-KEY` check for all endpoints.
    - *Status: Completed.*

- [ ] **Historical Detections API (CRITICAL)**:
    - **Task**: Create an endpoint `/detections/search` to fetch past detections.
    - **Filters**: Must support `camera_id`, `class_name`, and `date_range`.
    - **Dependency**: Hemant's Dashboard search bar depends on this.

- [ ] **Database Optimization**:
    - Ensure SQLite handles concurrent writes from multiple AI nodes efficiently.

---

## ✅ Progress Tracking
- 2026-05-06: Finished modularizing the hub and enforcing API security. Moving to Search API.
