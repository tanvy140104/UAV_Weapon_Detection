
import os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parents[2]
RUNTIME = BASE / "data" / "runtime"

for folder in ["temp", "ultralytics", "torch"]:
    (RUNTIME / folder).mkdir(parents=True, exist_ok=True)

os.environ["TMP"] = str(RUNTIME / "temp")
os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")

import cv2
from ultralytics import YOLO

MODEL = (
    BASE / "models" / "trained" /
    "gks_yolo11n_30e" / "weights" / "best.pt"
)

OUTPUT = BASE / "data" / "field_samples"


def save_sample(category, original, annotated):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    raw_dir = OUTPUT / category / "original"
    pred_dir = OUTPUT / category / "prediction"

    raw_dir.mkdir(parents=True, exist_ok=True)
    pred_dir.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(raw_dir / f"{stamp}.jpg"), original)
    cv2.imwrite(str(pred_dir / f"{stamp}.jpg"), annotated)

    print(f"Da luu mau [{category}]: {stamp}")


def main():
    if not MODEL.is_file():
        raise FileNotFoundError(MODEL)

    model = YOLO(str(MODEL))

    print("Classes:", model.names)
    print("===== THU THAP MAU LOI =====")
    print("Phim 1: Luu anh co DAO")
    print("Phim 2: Luu anh do vat KHONG PHAI VU KHI")
    print("Phim Q: Thoat")
    print("Du lieu luu tai:", OUTPUT)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        raise RuntimeError("Khong mo duoc webcam!")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while True:
            ok, frame = cap.read()

            if not ok:
                break

            # Confidence 0.25 chi de quan sat loi
            results = model.predict(
                frame,
                imgsz=640,
                conf=0.25,
                device=0,
                verbose=False
            )

            annotated = results[0].plot()

            cv2.putText(
                annotated,
                "1: KNIFE | 2: NORMAL | Q: QUIT",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

            cv2.imshow("GKS - Collect Errors", annotated)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("1"):
                save_sample("knife", frame, annotated)

            elif key == ord("2"):
                save_sample("normal", frame, annotated)

            elif key == ord("q") or key == 27:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
