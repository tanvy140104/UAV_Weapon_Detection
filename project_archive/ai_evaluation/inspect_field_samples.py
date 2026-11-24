
import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
RUNTIME = BASE / "data" / "runtime"

for name in ["temp", "ultralytics", "torch"]:
    (RUNTIME / name).mkdir(parents=True, exist_ok=True)

os.environ["TMP"] = str(RUNTIME / "temp")
os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")

from ultralytics import YOLO

MODEL = BASE / "models/trained/gks_yolo11n_30e/weights/best.pt"
SAMPLES = BASE / "data/field_samples"

model = YOLO(str(MODEL))

for category in ["knife", "normal"]:
    folder = SAMPLES / category / "original"

    for image_path in sorted(folder.glob("*.jpg")):
        results = model.predict(
            source=str(image_path),
            conf=0.05,
            imgsz=640,
            device=0,
            verbose=False
        )

        boxes = sorted(
            results[0].boxes,
            key=lambda b: float(b.conf[0]),
            reverse=True
        )

        print(f"\nANH: {image_path.name}")
        print("LOAI THUC TE:", category)

        if len(boxes) == 0:
            print("Khong co du doan tu 0.05")
            continue

        for box in boxes[:5]:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            label = model.names[class_id]

            print(f"  {label}: {confidence:.3f}")

print("\nKIEM TRA HOAN TAT")
