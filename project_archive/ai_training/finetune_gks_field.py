
import os
from pathlib import Path
from multiprocessing import freeze_support

# ==========================================
# 1. THIET LAP THU MUC TREN O D
# ==========================================

BASE = Path(__file__).resolve().parents[2]

RUNTIME = BASE / "runtime"
(RUNTIME / "ultralytics").mkdir(
    parents=True, exist_ok=True
)
(RUNTIME / "matplotlib").mkdir(
    parents=True, exist_ok=True
)
(RUNTIME / "torch").mkdir(
    parents=True, exist_ok=True
)
(RUNTIME / "temp").mkdir(
    parents=True, exist_ok=True
)

# Han che su dung o C
os.environ["YOLO_CONFIG_DIR"] = str(
    RUNTIME / "ultralytics"
)
os.environ["MPLCONFIGDIR"] = str(
    RUNTIME / "matplotlib"
)
os.environ["TORCH_HOME"] = str(
    RUNTIME / "torch"
)
os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["TMP"] = str(RUNTIME / "temp")

# ==========================================
# 2. IMPORT THU VIEN
# ==========================================

import torch
from ultralytics import YOLO


def main():

    # ======================================
    # 3. DUONG DAN MODEL VA DATASET
    # ======================================

    MODEL_PATH = (
        BASE
        / "models"
        / "trained"
        / "gks_yolo11n_30e"
        / "weights"
        / "best.pt"
    )

    DATA_YAML = (
        BASE
        / "data"
        / "combined_gks_field_finetune"
        / "data.yaml"
    )

    OUTPUT = BASE / "models" / "trained"
    RUN_NAME = "gks_field_ft_10e"

    # Kiem tra file
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(MODEL_PATH)

    if not DATA_YAML.is_file():
        raise FileNotFoundError(DATA_YAML)

    # Bao ve ket qua train cu va lan fine-tune
    run_dir = OUTPUT / RUN_NAME

    if run_dir.exists():
        raise FileExistsError(
            f"Thu muc ket qua da ton tai: {run_dir}\n"
            "Khong ghi de ket qua cu."
        )

    # ======================================
    # 4. KIEM TRA GPU
    # ======================================

    print("\n===== KIEM TRA THIET BI =====")
    print("PyTorch:", torch.__version__)
    print("CUDA:", torch.cuda.is_available())

    if not torch.cuda.is_available():
        raise RuntimeError(
            "Khong tim thay GPU CUDA. "
            "Dung huan luyen de kiem tra lai."
        )

    print("GPU:", torch.cuda.get_device_name(0))

    print("\n===== CAU HINH FINE-TUNE =====")
    print("Model:", MODEL_PATH)
    print("Dataset:", DATA_YAML)
    print("Output:", run_dir)
    print("Epochs: 10")
    print("Batch: 2")
    print("Mosaic: OFF")
    print("Workers: 0")
    print("Cache: OFF")

    # ======================================
    # 5. NAP MODEL TOT NHAT DA TRAIN
    # ======================================

    model = YOLO(str(MODEL_PATH))

    # ======================================
    # 6. BAT DAU FINE-TUNE
    # ======================================

    model.train(
        data=str(DATA_YAML),

        epochs=10,
        imgsz=640,
        batch=2,
        device=0,

        # Giam tai RAM laptop
        workers=0,
        cache=False,

        # Tat Mosaic de tranh loi RAM
        mosaic=0.0,
        mixup=0.0,
        copy_paste=0.0,

        # Learning rate nho cho fine-tune
        optimizer="AdamW",
        lr0=0.0005,
        lrf=0.1,
        warmup_epochs=1.0,

        # Ho tro CUDA
        amp=True,

        # Danh gia tren Validation
        val=True,
        patience=10,

        # Ket qua luu o D
        project=str(OUTPUT),
        name=RUN_NAME,
        exist_ok=False,

        # Luu checkpoint
        save=True,
        plots=False,

        # Lap lai thi nghiem
        seed=42,
    )

    # ======================================
    # 7. THONG BAO KET QUA
    # ======================================

    print("\n===== FINE-TUNE HOAN THANH =====")
    print("Thu muc:", run_dir)
    print("Best model:",
          run_dir / "weights" / "best.pt")
    print("Last model:",
          run_dir / "weights" / "last.pt")

    print("\nMODEL GKS 30 EPOCH GOC VAN DUOC GIU NGUYEN.")


if __name__ == "__main__":
    freeze_support()
    main()
