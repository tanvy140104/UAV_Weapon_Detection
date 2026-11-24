
from pathlib import Path

from ultralytics.data.utils import (
    check_det_dataset,
    img2label_paths
)

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# Cau hinh dataset ket hop
ROOT = BASE / "data" / "combined_gks_field_v1"
YAML = ROOT / "data.yaml"
TRAIN_LIST = ROOT / "train_images.txt"

print("===== KIEM TRA DATASET ULTRALYTICS =====")

# Kiem tra file data.yaml bang Ultralytics
data = check_det_dataset(
    str(YAML),
    autodownload=False
)

print("Train:", data["train"])
print("Validation:", data["val"])
print("Test:", data["test"])
print("Classes:", data["names"])

# Doc danh sach anh Train
images = [
    line.strip()
    for line in TRAIN_LIST.read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip()
]

# Dung ham chinh thuc cua Ultralytics
# de suy ra duong dan file nhan
labels = img2label_paths(images)

missing_images = [
    path for path in images
    if not Path(path).is_file()
]

missing_labels = [
    path for path in labels
    if not Path(path).is_file()
]

print("\n===== KET QUA =====")
print("Tong anh Train:", len(images))
print("Tong nhan suy ra:", len(labels))
print("Anh bi thieu:", len(missing_images))
print("Nhan bi thieu:", len(missing_labels))

if missing_images:
    print("Vi du anh thieu:", missing_images[:3])

if missing_labels:
    print("Vi du nhan thieu:", missing_labels[:3])

if (
    len(images) == 7112
    and len(labels) == 7112
    and not missing_images
    and not missing_labels
):
    print("\nDATASET SAN SANG DE FINE-TUNE!")
else:
    print("\nCAN SUA DATASET TRUOC KHI TRAIN!")
