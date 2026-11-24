
import os
from pathlib import Path

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# Chuyen cache va file tam sang o D
RUNTIME = BASE / "data" / "runtime"

for folder in ["temp", "ultralytics", "matplotlib", "torch"]:
    (RUNTIME / folder).mkdir(parents=True, exist_ok=True)

os.environ["TMP"] = str(RUNTIME / "temp")
os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["TMPDIR"] = str(RUNTIME / "temp")
os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["MPLCONFIGDIR"] = str(RUNTIME / "matplotlib")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")

import torch
from ultralytics import YOLO


def main():

    # Model YOLO11n goc da tai
    MODEL = BASE / "models" / "yolo11n.pt"

    # Dataset 3 lop: knife, stick, gun
    DATA = BASE / "data" / "weapons_gks_v1" / "data.yaml"

    # Thu muc luu ket qua train
    OUTPUT = BASE / "models" / "trained"

    if not MODEL.is_file():
        raise FileNotFoundError(MODEL)

    if not DATA.is_file():
        raise FileNotFoundError(DATA)

    # Bat buoc co GPU NVIDIA
    if not torch.cuda.is_available():
        raise RuntimeError("Khong tim thay CUDA GPU!")

    print("\n===== CAU HINH HUAN LUYEN =====")
    print("GPU:", torch.cuda.get_device_name(0))
    print("Model:", MODEL)
    print("Dataset:", DATA)
    print("Epochs: 30")
    print("Batch: 4")
    print("Image size: 640")
    print("AMP: False")
    print("Output:", OUTPUT)

    # Nap model pretrained ban dau
    model = YOLO(str(MODEL))

    # Huan luyen chinh thuc
    model.train(
        data=str(DATA),

        # Toan bo du lieu Train
        fraction=1.0,

        # So lan huan luyen
        epochs=30,

        # Cau hinh phu hop GTX 1650 4GB
        imgsz=640,
        batch=4,
        device=0,
        workers=0,

        # Tat AMP theo canh bao GPU
        amp=False,

        # Khong nap tat ca anh vao RAM
        cache=False,

        # Danh gia tren tap Validation
        val=True,

        # Luu model va bieu do
        save=True,
        plots=True,

        # Dat patience bang so epoch
        patience=30,

        # Luu tren o D
        project=str(OUTPUT),
        name="gks_yolo11n_30e",

        # Tranh ghi de ket qua cu
        exist_ok=False,

        # Ket qua co the tai lap
        seed=42
    )

    # Thu muc ket qua thuc te
    result_dir = Path(model.trainer.save_dir)

    print("\n===== HUAN LUYEN HOAN TAT =====")
    print("Ket qua:", result_dir)
    print("Best model:", result_dir / "weights" / "best.pt")
    print("Last model:", result_dir / "weights" / "last.pt")


if __name__ == "__main__":
    main()
