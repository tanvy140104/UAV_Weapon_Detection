
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import math
import os

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# File ZIP goc de doi chieu anh
ZIP_FILE = BASE / "data/Gun-Knife-Stick Detection.v5i.yolov11.zip"

# Thu muc nhan da chuan hoa
LABELS = BASE / "data/prepared/gun_knife_stick_v5/labels"

# Ho tro ten file dai tren Windows
def long_path(path):
    path = str(path.resolve())
    if os.name == "nt":
        return "\\\\?\\" + path
    return path

errors = []
class_counts = Counter()
split_counts = Counter()
total_boxes = 0

# Lay danh sach anh va file nhan tu ZIP
with ZipFile(ZIP_FILE) as z:
    names = z.namelist()

    image_stems = {
        (n.split("/")[0], Path(n).stem)
        for n in names
        if "/images/" in n
        and n.split("/")[0] in ("train", "valid", "test")
        and n.lower().endswith((".jpg", ".jpeg", ".png"))
    }

    label_names = [
        n for n in names
        if "/labels/" in n
        and n.split("/")[0] in ("train", "valid", "test")
        and n.endswith(".txt")
    ]

# Kiem tra tung file nhan da chuan hoa
for name in label_names:
    split, _, filename = name.split("/")

    label_file = LABELS / split / filename

    # Kiem tra anh tuong ung
    if (split, Path(filename).stem) not in image_stems:
        errors.append(f"Thieu anh: {name}")

    # Doc nhan, ho tro duong dan dai
    try:
        with open(long_path(label_file), encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        errors.append(f"Khong doc duoc nhan: {name}")
        continue

    split_counts[split] += 1

    for line in lines:
        if not line.strip():
            continue

        parts = line.split()

        if len(parts) != 5:
            errors.append(f"Sai dinh dang: {name}")
            continue

        try:
            cls = int(parts[0])
            x, y, w, h = map(float, parts[1:])
        except ValueError:
            errors.append(f"Sai gia tri: {name}")
            continue

        # Kiem tra ID, toa do va kich thuoc
        valid = (
            cls in (0, 1, 2)
            and all(math.isfinite(v) for v in (x, y, w, h))
            and w > 0 and h > 0
            and 0 <= x - w / 2
            and x + w / 2 <= 1
            and 0 <= y - h / 2
            and y + h / 2 <= 1
        )

        if not valid:
            errors.append(f"Khung bao loi: {name}")
            continue

        class_counts[cls] += 1
        total_boxes += 1

print("\n===== KIEM TRA DATASET =====")
print("Tong file nhan:", sum(split_counts.values()))
print("Tong bounding box hop le:", total_boxes)

for split in ("train", "valid", "test"):
    print(split.upper(), ":", split_counts[split])

print("Knife:", class_counts[0])
print("Stick:", class_counts[1])
print("Gun:", class_counts[2])

print("\nSo loi phat hien:", len(errors))

for error in errors[:10]:
    print("LOI:", error)

if not errors:
    print("KIEM TRA THANH CONG!")
