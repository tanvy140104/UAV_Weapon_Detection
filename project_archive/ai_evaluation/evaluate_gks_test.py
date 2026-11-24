
import os
from pathlib import Path

# Thu muc du an
BASE = Path(__file__).resolve().parents[2]

# Chuyen cache, file tam sang o D
RUNTIME = BASE / "data" / "runtime"

for folder in ["temp", "ultralytics", "matplotlib", "torch"]:
    (RUNTIME / folder).mkdir(parents=True, exist_ok=True)

os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["TMP"] = str(RUNTIME / "temp")
os.environ["TMPDIR"] = str(RUNTIME / "temp")
os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["MPLCONFIGDIR"] = str(RUNTIME / "matplotlib")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")

import torch
from ultralytics import YOLO


def main():

    # Model tot nhat sau 30 epoch
    MODEL = (
        BASE / "models" / "trained" /
        "gks_yolo11n_30e" / "weights" / "best.pt"
    )

    # Dataset 3 lop
    DATA = (
        BASE / "data" / "weapons_gks_v1" / "data.yaml"
    )

    # Luu ket qua danh gia tren o D
    OUTPUT = BASE / "models" / "evaluation"

    if not MODEL.is_file():
        raise FileNotFoundError(MODEL)

    if not DATA.is_file():
        raise FileNotFoundError(DATA)

    if not torch.cuda.is_available():
        raise RuntimeError("Khong tim thay CUDA GPU!")

    print("===== DANH GIA TAP TEST =====")
    print("GPU:", torch.cuda.get_device_name(0))
    print("Model:", MODEL)
    print("Dataset:", DATA)
    print("Tap danh gia: TEST")
    print("Batch: 2")

    # Nap model da huan luyen
    model = YOLO(str(MODEL))

    # Danh gia tren tap Test, khong train them
    metrics = model.val(
        data=str(DATA),
        split="test",
        imgsz=640,
        batch=2,
        device=0,
        workers=0,
        plots=True,
        project=str(OUTPUT),
        name="gks_test_30e",
        exist_ok=True,
    )

    # In cac chi so danh gia
    print("\n===== KET QUA TEST =====")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall: {metrics.box.mr:.4f}")
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")

    print("\nDA DANH GIA XONG!")
    print("Ket qua luu trong:", OUTPUT / "gks_test_30e")


if __name__ == "__main__":
    main()
