
import os
from pathlib import Path
from datetime import datetime

# ==========================================
# 1. CAU HINH THU MUC TREN O D
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
import numpy as np
import torch
from ultralytics import YOLO

# ==========================================
# 2. DUONG DAN HAI MODEL
# ==========================================

OLD_MODEL = (
    BASE / "models" / "trained"
    / "gks_yolo11n_30e"
    / "weights" / "best.pt"
)

NEW_MODEL = (
    BASE / "models" / "trained"
    / "gks_field_ft_10e"
    / "weights" / "best.pt"
)

SAVE_DIR = (
    BASE / "data" / "field_samples"
    / "ab_comparison"
)
SAVE_DIR.mkdir(parents=True, exist_ok=True)

if not OLD_MODEL.is_file():
    raise FileNotFoundError(OLD_MODEL)

if not NEW_MODEL.is_file():
    raise FileNotFoundError(NEW_MODEL)

if not torch.cuda.is_available():
    raise RuntimeError("Khong tim thay GPU CUDA!")

# ==========================================
# 3. NAP HAI MODEL
# ==========================================

print("Dang nap model goc...")
model_old = YOLO(str(OLD_MODEL))

print("Dang nap model fine-tune...")
model_new = YOLO(str(NEW_MODEL))

# ==========================================
# 4. MO WEBCAM
# ==========================================

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    raise RuntimeError("Khong mo duoc webcam!")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

CONF = 0.25

print("\n===== SO SANH HAI MODEL =====")
print("Ben trai: Model goc 30 epoch")
print("Ben phai: Model fine-tune 10 epoch")
print("Nhan S: Luu anh so sanh")
print("Nhan Q hoac ESC: Thoat")

# ==========================================
# 5. NHAN DIEN CUNG MOT KHUNG HINH
# ==========================================

try:
    while True:

        ok, frame = cap.read()

        if not ok:
            print("Khong doc duoc khung hinh!")
            break

        # Cung mot frame cho ca hai model
        result_old = model_old.predict(
            source=frame,
            imgsz=640,
            conf=CONF,
            device=0,
            verbose=False
        )[0]

        result_new = model_new.predict(
            source=frame,
            imgsz=640,
            conf=CONF,
            device=0,
            verbose=False
        )[0]

        # Ve khung nhan dien
        view_old = result_old.plot()
        view_new = result_new.plot()

        # Dua ve cung kich thuoc
        view_old = cv2.resize(view_old, (640, 360))
        view_new = cv2.resize(view_new, (640, 360))

        # Ghi ten model
        cv2.putText(
            view_old,
            "MODEL GOC - 30 EPOCH",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        cv2.putText(
            view_new,
            "FINE-TUNE - 10 EPOCH",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        # Ghep hai ket qua canh nhau
        combined = np.hstack((view_old, view_new))

        cv2.imshow("YOLO11n - A/B Comparison", combined)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            filename = (
                "compare_"
                + datetime.now().strftime("%Y%m%d_%H%M%S")
                + ".jpg"
            )

            path = SAVE_DIR / filename
            cv2.imwrite(str(path), combined)
            print("Da luu:", path)

        if key in [ord("q"), 27]:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()

print("DA KET THUC SO SANH!")
