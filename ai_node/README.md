# AI Edge Node

This node runs object detection using YOLOv5 and sends detection events to the central backend.

## 🚀 Getting Started

### 1. Setup Environment
```bash
python -m venv venv
powershell: .\venv\Scripts\Activate
bash: source venv/bin/activate
pip install -r yolov5/requirements.txt requests
```

### 2. Run Object Detection Server
To run the included Flask REST API:
```bash
python yolov5/utils/flask_rest_api/restapi.py --port 5000
```

### 3. (PROPER) Run Real-time Intelligence Node
To run the proper YOLOv5 node that processes your mobile live feed and pushes real intelligence to the Fog Hub:
```bash
# Ensure you are in ai_node/
.\venv\Scripts\Activate
python proper_yolo_node.py
```

This script will:
1. Load a real pre-trained YOLOv5 model.
2. Hook into your Mobile-Cam stream.
3. Perform real-time object detection (Persons, vehicles, objects).
4. Send precise coordinates to the Dashboard.
