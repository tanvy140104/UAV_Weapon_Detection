
import os
from pathlib import Path
from collections import Counter

# =====================================
# 1. CAU HINH DUONG DAN TREN O D
# =====================================

BASE = Path(__file__).resolve().parents[2]

CONFIG = BASE / "runtime" / "ultralytics"
MPL = BASE / "runtime" / "matplotlib"

CONFIG.mkdir(parents=True, exist_ok=True)
MPL.mkdir(parents=True, exist_ok=True)

# Han che Ultralytics ghi vao o C
os.environ["YOLO_CONFIG_DIR"] = str(CONFIG)
os.environ["MPLCONFIGDIR"] = str(MPL)

from ultralytics.data.base import BaseDataset
from ultralytics.data.utils import img2label_paths

ROOT = BASE / "data" / "combined_gks_field_finetune"

TRAIN_LIST = ROOT / "train_images.txt"

FIELD_DIR = (
    BASE / "data" / "prepared"
    / "field_webcam_v1" / "images" / "train"
).resolve()


# =====================================
# 2. DOC DANH SACH BANG ULTRALYTICS
# =====================================

reader = BaseDataset.__new__(BaseDataset)
reader.prefix = "Train: "
reader.fraction = 1.0

images = reader.get_img_files(str(TRAIN_LIST))
labels = img2label_paths(images)

# Dem so lan xuat hien cua moi anh
counts = Counter(str(Path(p).resolve()) for p in images)

field_counts = {
    p: n for p, n in counts.items()
    if Path(p).parent == FIELD_DIR
}

gks_counts = {
    p: n for p, n in counts.items()
    if Path(p).parent != FIELD_DIR
}

# =====================================
# 3. KIEM TRA ANH VA NHAN
# =====================================

missing_images = [
    p for p in images
    if not Path(p).is_file()
]

missing_labels = [
    p for p in labels
    if not Path(p).is_file()
]

print("\n===== KIEM TRA FINE-TUNE =====")

print("Tong luot anh:", len(images))
print("Anh duy nhat:", len(counts))

print("GKS duy nhat:", len(gks_counts))
print("Webcam duy nhat:", len(field_counts))

print("Luot GKS:", sum(gks_counts.values()))
print("Luot Webcam:", sum(field_counts.values()))

print("Anh thieu:", len(missing_images))
print("Nhan thieu:", len(missing_labels))

# Kiem tra moi anh webcam xuat hien dung 5 lan
field_repeat_ok = all(
    n == 5 for n in field_counts.values()
)

gks_repeat_ok = all(
    n == 1 for n in gks_counts.values()
)

valid = (
    len(images) == 7352
    and len(counts) == 7112
    and len(gks_counts) == 7052
    and len(field_counts) == 60
    and field_repeat_ok
    and gks_repeat_ok
    and not missing_images
    and not missing_labels
)

if valid:
    print("\nKIEM TRA THANH CONG!")
    print("ULTRALYTICS DOC DUNG 7352 LUOT ANH.")
    print("SAN SANG CHUAN BI FINE-TUNE!")
else:
    print("\nCO LOI - CHUA NEN TRAIN.")
