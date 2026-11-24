
import os
from pathlib import Path

# ==========================================
# 1. THU MUC DU AN TREN O D
# ==========================================

BASE = Path(__file__).resolve().parents[2]
RUNTIME = BASE / "runtime"

for name in ["ultralytics", "matplotlib", "torch", "temp"]:
    (RUNTIME / name).mkdir(parents=True, exist_ok=True)

os.environ["YOLO_CONFIG_DIR"] = str(RUNTIME / "ultralytics")
os.environ["MPLCONFIGDIR"] = str(RUNTIME / "matplotlib")
os.environ["TORCH_HOME"] = str(RUNTIME / "torch")
os.environ["TEMP"] = str(RUNTIME / "temp")
os.environ["TMP"] = str(RUNTIME / "temp")

from ultralytics import YOLO
import torch

# ==========================================
# 2. KHAI BAO MODEL VA DATASET
# ==========================================

MODEL = (
    BASE / "models" / "trained"
    / "gks_field_ft_10e" / "weights" / "best.pt"
)

DATA = (
    BASE / "data" / "combined_gks_field_finetune"
    / "data.yaml"
)

OUTPUT = BASE / "models" / "evaluation"
RUN_NAME = "gks_field_ft_10e_test"

if not MODEL.is_file():
    raise FileNotFoundError(MODEL)

if not DATA.is_file():
    raise FileNotFoundError(DATA)

if (OUTPUT / RUN_NAME).exists():
    raise FileExistsError(
        "Ket qua Test da ton tai. Khong ghi de."
    )

if not torch.cuda.is_available():
    raise RuntimeError("Khong tim thay CUDA!")

# ==========================================
# 3. DANH GIA TREN TAP TEST
# ==========================================

print("===== DANH GIA MODEL FINE-TUNE =====")
print("Model:", MODEL)
print("Dataset:", DATA)
print("GPU:", torch.cuda.get_device_name(0))

model = YOLO(str(MODEL))

metrics = model.val(
    data=str(DATA),
    split="test",
    imgsz=640,
    batch=2,
    device=0,
    workers=0,
    plots=False,
    project=str(OUTPUT),
    name=RUN_NAME,
    exist_ok=False,
    verbose=True,
)

# ==========================================
# 4. IN VA LUU KET QUA
# ==========================================

p = float(metrics.box.mp)
r = float(metrics.box.mr)
map50 = float(metrics.box.map50)
map5095 = float(metrics.box.map)

summary = (
    "===== KET QUA TEST MODEL FINE-TUNE =====\n"
    f"Precision: {p:.4f}\n"
    f"Recall: {r:.4f}\n"
    f"mAP50: {map50:.4f}\n"
    f"mAP50-95: {map5095:.4f}\n"
)

print("\n" + summary)

result_file = OUTPUT / RUN_NAME / "summary.txt"
result_file.write_text(summary, encoding="utf-8")

print("Da luu ket qua:", result_file)
print("DANH GIA HOAN THANH!")
