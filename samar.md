# 🔴 Samar's Task List (Backend & Core)

Samar, you are responsible for the heart of the system—the Central Hub.

---

## 🚀 Current Tasks

- [ ] **Backend Modularization**: 
    - Split `main.py` into `models.py`, `database.py`, `manager.py`, and `routes/`.
    - Current `main.py` is too large and risky.

- [ ] **Security Enforcement**:
    - Implement a consistent `X-API-KEY` check for all endpoints.
    - Default Key: `surveillance_secret_key_2024` (should be in `.env`).

- [ ] **Environment Configuration**:
    - Move all hardcoded values (DB URL, Port, API Key) to a `.env` file.

- [ ] **Historical Detections API**:
    - Create an endpoint to fetch past detections with filters (by date, class, or camera).

---

## 🛠️ Tech Note (Production Gap)
Our current frontend (`index.html`) is failing because it doesn't send the API key. Please ensure your backend changes don't break the system until the new Dashboard is ready.

---

## ✅ Progress Tracking
*Update this file whenever you finish a task!*
