
import os
from pathlib import Path

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# Luu cache va file tam tren o D, tranh day o C
RUNTIME = BASE / "data" / "runtime"

for folder in ["temp", "ultralytics", "matplotlib", "torch"]:
    (RUNTIME / folder).mkdir(parents=True, exist_ok=True)

os.environ["TMP"] = str(RUNTIME / "temp")
os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["MPLCONFIGDIR"] = str(RUNTIME / "matplotlib")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")

import torch
from ultralytics import YOLO

# Duong dan model YOLO11n da tai truoc do
MODEL = BASE / "models" / "yolo11n.pt"

# Dataset 3 lop da chuan hoa
DATA = BASE / "data" / "weapons_gks_v1" / "data.yaml"

# Noi luu ket qua train tren o D
OUTPUT = BASE / "models" / "trained"

# Kiem tra file dau vao
if not MODEL.is_file():
    raise FileNotFoundError(f"Khong tim thay model: {MODEL}")

if not DATA.is_file():
    raise FileNotFoundError(f"Khong tim thay data.yaml: {DATA}")

# Bat buoc su dung GPU NVIDIA
if not torch.cuda.is_available():
    raise RuntimeError("Khong phat hien CUDA GPU!")

print("===== KIEM TRA GPU =====")
print("PyTorch:", torch.__version__)
print("CUDA:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0))
print("Model:", MODEL)
print("Dataset:", DATA)

# Nap model YOLO11n
model = YOLO(str(MODEL))

# CHAY THU: 1 epoch voi 2% du lieu Train
# Batch 2 de han che loi tran VRAM 4 GB
model.train(
    data=str(DATA),
    epochs=1,
    fraction=0.02,
    imgsz=640,
    batch=2,
    device=0,
    workers=0,
    cache=False,
    amp=True,
    project=str(OUTPUT),
    name="gks_gpu_test",
    exist_ok=True,
    plots=False,
    val=False,
    save=True,
)

print("\n===== KET QUA =====")
print("HUAN LUYEN THU THANH CONG!")
print("GPU:", torch.cuda.get_device_name(0))
print("Ket qua luu tai:", OUTPUT / "gks_gpu_test")
