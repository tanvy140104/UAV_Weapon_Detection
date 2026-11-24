
import os
import time
from pathlib import Path

# Thu muc du an
BASE = Path(__file__).resolve().parents[2]

# Giu cache va file tam tren o D
RUNTIME = BASE / "data" / "runtime"

for folder in ["temp", "ultralytics", "torch"]:
    (RUNTIME / folder).mkdir(parents=True, exist_ok=True)

os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["TMP"] = str(RUNTIME / "temp")
os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")

import cv2
import torch
from ultralytics import YOLO

# Model da huan luyen 30 epoch
MODEL_PATH = (
    BASE / "models" / "trained" /
    "gks_yolo11n_30e" / "weights" / "best.pt"
)

# Camera laptop
CAMERA_ID = 0

# Nguong tin cay ban dau
CONFIDENCE = 0.60


def main():

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(MODEL_PATH)

    if not torch.cuda.is_available():
        raise RuntimeError("Khong tim thay GPU CUDA!")

    # Nap model da huan luyen
    model = YOLO(str(MODEL_PATH))

    print("===== TEST AI WEBCAM =====")
    print("GPU:", torch.cuda.get_device_name(0))
    print("Model:", MODEL_PATH)
    print("Classes:", model.names)
    print("Nhan Q hoac ESC de thoat")

    # Mo camera tren Windows
    cap = cv2.VideoCapture(
        CAMERA_ID,
        cv2.CAP_DSHOW
    )

    if not cap.isOpened():
        raise RuntimeError(
            "Khong mo duoc camera laptop!"
        )

    # Dat do phan giai camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while True:

            ok, frame = cap.read()

            if not ok:
                print("Khong doc duoc frame camera!")
                break

            start = time.perf_counter()

            # Nhan dien 3 lop vu khi bang GPU
            results = model.predict(
                source=frame,
                imgsz=640,
                conf=CONFIDENCE,
                device=0,
                verbose=False
            )

            # Ve khung va nhan len hinh
            output = results[0].plot()

            # Tinh FPS xu ly
            elapsed = time.perf_counter() - start
            fps = 1.0 / max(elapsed, 1e-6)

            cv2.putText(
                output,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # Hien thi video nhan dien
            cv2.imshow(
                "UAV Weapon Detection - YOLO11",
                output
            )

            # Nhan Q hoac ESC de thoat
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break

    finally:
        # Giai phong camera
        cap.release()
        cv2.destroyAllWindows()

    print("DA DUNG TEST WEBCAM")


if __name__ == "__main__":
    main()
