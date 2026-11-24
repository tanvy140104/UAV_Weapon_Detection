
import os
import threading
from pathlib import Path

# ==========================================
# 1. CAU HINH DUONG DAN TREN O D
# ==========================================

BASE = Path(__file__).resolve().parents[2]
RUNTIME = BASE / "runtime"

for folder in ["ultralytics", "matplotlib", "torch", "temp"]:
    (RUNTIME / folder).mkdir(parents=True, exist_ok=True)

os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["MPLCONFIGDIR"] = str(RUNTIME / "matplotlib")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")
os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["TMP"] = str(RUNTIME / "temp")

import cv2
import torch
from ultralytics import YOLO

# ==========================================
# 2. CAU HINH MO HINH
# ==========================================

MODEL_PATH = (
    BASE / "models" / "trained"
    / "gks_field_ft_10e"
    / "weights" / "best.pt"
)

CONFIDENCE = 0.35
IMAGE_SIZE = 640

CLASS_NAMES = {
    0: "knife",
    1: "stick",
    2: "gun"
}

_model = None
_model_lock = threading.RLock()


# ==========================================
# 3. NAP MODEL MOT LAN
# ==========================================

def _load_model():
    global _model

    if _model is None:

        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Khong tim thay model: {MODEL_PATH}"
            )

        print("Dang nap YOLO11n:", MODEL_PATH)

        _model = YOLO(str(MODEL_PATH))

        print("Nap model thanh cong!")

    return _model


# ==========================================
# 4. NHAN DIEN TREN MOT FRAME
# ==========================================

def get_model():
    with _model_lock:
        return _load_model()


def detect_frame(frame):
    with _model_lock:
        return _detect_frame(frame)


def _detect_frame(frame):

    if frame is None or frame.size == 0:
        raise ValueError("Frame rong hoac khong hop le!")

    model = get_model()

    device = 0 if torch.cuda.is_available() else "cpu"

    result = model.predict(
        source=frame,
        imgsz=IMAGE_SIZE,
        conf=CONFIDENCE,
        device=device,
        verbose=False
    )[0]

    detections = []

    for box in result.boxes:

        class_id = int(box.cls[0].item())
        confidence = float(box.conf[0].item())

        x1, y1, x2, y2 = (
            box.xyxy[0].cpu().tolist()
        )

        detections.append({
            "class_id": class_id,
            "label": CLASS_NAMES.get(
                class_id, str(class_id)
            ),
            "confidence": round(confidence, 4),
            "bbox": {
                "x1": round(x1, 1),
                "y1": round(y1, 1),
                "x2": round(x2, 1),
                "y2": round(y2, 1)
            }
        })

    return detections


# ==========================================
# 5. NHAN DIEN TREN FILE ANH
# ==========================================

def detect_image(image_path):

    image_path = Path(image_path)

    if not image_path.is_absolute():
        image_path = BASE / image_path

    if not image_path.is_file():
        raise FileNotFoundError(image_path)

    frame = cv2.imread(str(image_path))

    if frame is None:
        raise RuntimeError(
            f"Khong doc duoc anh: {image_path}"
        )

    return detect_frame(frame)
