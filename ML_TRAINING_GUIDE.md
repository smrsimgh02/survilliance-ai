# 🧠 ML Training Guide: Custom Threat Detection

This guide explains how to train a custom YOLOv5 model for our Surveillance AI system using Google Colab.

---

## 🎯 Objective
To detect specific threats such as **Weapons (Guns/Knives)**, **Fire**, or **Suspicious Objects** that are not part of the standard COCO dataset.

---

## 🛠️ Step 1: Data Preparation (Roboflow)
1.  Go to [Roboflow Universe](https://universe.roboflow.com/).
2.  Search for datasets like "Weapon Detection" or "CCTV Fire Detection".
3.  Export the dataset in **YOLOv5 PyTorch** format.
4.  You will get a `data.yaml` file and folders for `train/` and `val/` images.

---

## ☁️ Step 2: Training on Google Colab
Use the free GPU on Colab to speed up training.

1.  **Clone YOLOv5 Repository**:
    ```python
    !git clone https://github.com/ultralytics/yolov5
    %cd yolov5
    !pip install -r requirements.txt
    ```

2.  **Upload your Dataset**:
    Upload the zip file from Roboflow and unzip it in the Colab environment.

3.  **Start Training**:
    ```python
    !python train.py --img 640 --batch 16 --epochs 50 --data /path/to/data.yaml --weights yolov5s.pt --cache
    ```
    *Note: 50 epochs is a good start for weapons detection.*

4.  **Download Results**:
    After training, go to `yolov5/runs/train/exp/weights/` and download **`best.pt`**.

---

## 🔌 Step 3: Integration into our AI Node
Once you have `best.pt`, follow these steps to use it in our project:

1.  Place `best.pt` inside the `ai_node/` directory.
2.  Update the model loading logic in `proper_yolo_node.py`:
    ```python
    # Change this:
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
    
    # To this:
    model = torch.hub.load('ultralytics/yolov5', 'custom', path='ai_node/best.pt')
    ```

---

## ⚠️ Important Tips
- **Lighting**: Ensure your dataset has images from night-vision or low-light CCTV cameras for better real-world accuracy.
- **False Positives**: Include "background" images (images with no threats) to reduce false alarms.
- **Hardware**: For production, we might need to export the model to **ONNX** or **TensorRT** for even faster performance.

---

*Authored by Vishal & AI Assistant*
