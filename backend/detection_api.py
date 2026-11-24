
import os
from pathlib import Path

# ==========================================
# 1. CAU HINH THU MUC TREN O D
# ==========================================

BASE = Path(__file__).resolve().parents[1]
RUNTIME = BASE / "runtime"

for name in ["ultralytics", "matplotlib", "torch", "temp"]:
    (RUNTIME / name).mkdir(parents=True, exist_ok=True)

os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["MPLCONFIGDIR"] = str(RUNTIME / "matplotlib")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")
os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["TMP"] = str(RUNTIME / "temp")

# ==========================================
# 2. IMPORT THU VIEN
# ==========================================

import cv2
import numpy as np
import torch

from fastapi import FastAPI, APIRouter, Request, HTTPException
from starlette.concurrency import run_in_threadpool

from backend.services.detection_service import (
    detect_frame,
    MODEL_PATH,
    CLASS_NAMES
)

# ==========================================
# 3. TAO FASTAPI VA ROUTER
# ==========================================

app = FastAPI(
    title="UAV Weapon Detection API",
    description="API nhan dien dao, gay, sung bang YOLO11n",
    version="1.0"
)

router = APIRouter(
    prefix="/api/detection",
    tags=["AI Detection"]
)

# Gioi han anh tai len: 10 MB
MAX_IMAGE_BYTES = 10 * 1024 * 1024


# ==========================================
# 4. API KIEM TRA TRANG THAI
# ==========================================

@router.get("/health")
def detection_health():

    return {
        "status": "READY" if MODEL_PATH.is_file() else "MODEL_MISSING",
        "model": MODEL_PATH.name,
        "model_exists": MODEL_PATH.is_file(),
        "cuda_available": torch.cuda.is_available(),
        "classes": CLASS_NAMES
    }


# ==========================================
# 5. API NHAN DIEN ANH
# ==========================================

@router.post("/image")
async def detect_image_api(request: Request):

    # Nhan anh JPEG hoac PNG dang binary
    content_type = request.headers.get(
        "content-type", ""
    ).split(";")[0].strip().lower()

    if content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=415,
            detail="Chi ho tro image/jpeg hoac image/png"
        )

    # Doc du lieu anh tu HTTP request
    image_bytes = bytearray()
    async for chunk in request.stream():
        if len(image_bytes) + len(chunk) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Image exceeds 10 MB")
        image_bytes.extend(chunk)

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Du lieu anh rong"
        )

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Anh vuot qua 10 MB"
        )

    # Chuyen bytes thanh anh OpenCV
    np_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    frame = cv2.imdecode(
        np_array,
        cv2.IMREAD_COLOR
    )

    if frame is None:
        raise HTTPException(
            status_code=400,
            detail="Khong giai ma duoc anh"
        )

    # Goi AI DetectionService
    # Chay tren thread de khong chan event loop
    try:
        detections = await run_in_threadpool(detect_frame, frame)
    except (FileNotFoundError, RuntimeError) as error:
        import logging
        logging.getLogger(__name__).exception("Image detection unavailable")
        raise HTTPException(status_code=503, detail="AI detection unavailable. See server log.") from error

    height, width = frame.shape[:2]

    # Tra ket qua cho Frontend
    return {
        "status": "SUCCESS",
        "image_width": width,
        "image_height": height,
        "detection_count": len(detections),
        "has_weapon": len(detections) > 0,
        "detections": detections
    }


# ==========================================
# 6. DANG KY ROUTER
# ==========================================

app.include_router(router)


# ==========================================
# 7. API TRANG CHU
# ==========================================

@app.get("/")
def home():

    return {
        "project": "UAV Weapon Detection",
        "backend": "FastAPI",
        "ai_model": "YOLO11n",
        "message": "Backend AI dang hoat dong"
    }
