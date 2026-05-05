# 📊 Frontend Analysis & Production Gaps

This document details the analysis of the current prototype (`backend/static/index.html`) and the steps needed to make it production-ready.

---

## 🔍 Current State Analysis
The current `index.html` is a high-fidelity prototype using Vanilla JavaScript and Canvas. While it looks good, it has several critical flaws.

### 1. Authentication Failure (Critical)
The backend was recently updated by Samar to require an `X-API-KEY`. However, the frontend does not include this header in its `fetch()` or `WebSocket` requests.
- **Impact**: Camera registration and detection updates will fail.
- **Fix**: Add headers to all API calls.

### 2. Rendering & Alignment
The bounding boxes are drawn on a `<canvas>` overlaid on an `<img>`.
- **Bug**: The alignment logic uses `setInterval`, which is unreliable and causes boxes to drift or offset during window resizing.
- **Fix**: Use `ResizeObserver` to sync canvas and image dimensions perfectly.

### 3. Error Handling
The code uses empty `catch` blocks or simple alerts.
- **Gap**: There is no feedback for the user if the server is down or the WebSocket disconnects.
- **Fix**: Implement a toast notification system and auto-reconnect UI states.

### 4. Code Architecture
The code is monolithic (400+ lines in one file).
- **Gap**: Hard to scale, test, or add new features like "Search" or "Maps".
- **Fix**: Transition to a modular **React** application (Vite + TypeScript).

---

## 🛠️ Requirements for New Dashboard (Hemant)
1. **Tech Stack**: React, Vite, Tailwind CSS (optional), Axios, Socket.io-client.
2. **Security**: Support for `X-API-KEY` from a `.env` file or login.
3. **Features**: Live stream, bounding boxes, detection history, and node management.
