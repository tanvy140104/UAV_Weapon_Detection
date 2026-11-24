
import os
import shutil
from pathlib import Path

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# Luu file tam va cache tren o D
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

    # Checkpoint da huan luyen xong 2 epoch
    CHECKPOINT = (
        BASE / "models" / "trained" /
        "gks_yolo11n_30e" / "weights" / "last.pt"
    )

    # Noi sao luu checkpoint de tranh mat du lieu
    BACKUP = (
        BASE / "models" / "trained" /
        "checkpoint_backup" / "last_after_epoch2.pt"
    )

    if not CHECKPOINT.is_file():
        raise FileNotFoundError(CHECKPOINT)

    if not torch.cuda.is_available():
        raise RuntimeError("Khong tim thay GPU CUDA!")

    # Sao luu checkpoint truoc khi tiep tuc
    BACKUP.parent.mkdir(parents=True, exist_ok=True)

    if not BACKUP.exists():
        shutil.copy2(CHECKPOINT, BACKUP)
        print("Da sao luu checkpoint:", BACKUP)

    print("\n===== TIEP TUC HUAN LUYEN =====")
    print("GPU:", torch.cuda.get_device_name(0))
    print("Checkpoint:", CHECKPOINT)
    print("Epoch da hoan thanh: 2")
    print("Epoch muc tieu: 30")
    print("Batch moi: 2")
    print("Tat Mosaic tu Epoch 3")

    # Nap checkpoint cu
    model = YOLO(str(CHECKPOINT))

    # Resume giu trang thai optimizer va epoch
    model.train(
        resume=True,
        device=0,
        batch=2,

        # 30 - 28 = 2 (epoch index)
        # Tat Mosaic khi bat dau Epoch 3
        close_mosaic=28,
    )

    print("\n===== HUAN LUYEN HOAN TAT =====")
    print("Ket qua:", model.trainer.save_dir)


if __name__ == "__main__":
    main()
