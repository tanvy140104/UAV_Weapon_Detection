
from pathlib import Path
from zipfile import ZipFile
from collections import defaultdict
import hashlib

# Thu muc du an
BASE = Path(__file__).resolve().parents[2]

# Dataset goc
ZIP_FILE = (
    BASE / "data" /
    "Gun-Knife-Stick Detection.v5i.yolov11.zip"
)

# Luu danh sach anh co noi dung trung nhau
hashes = defaultdict(list)

total_images = 0

# Doc truc tiep tu ZIP, khong giai nen lai
with ZipFile(ZIP_FILE) as z:

    for name in z.namelist():

        parts = name.split("/")

        # Chi kiem tra anh Train, Valid, Test
        if len(parts) != 3:
            continue

        split, folder, filename = parts

        if split not in ("train", "valid", "test"):
            continue

        if folder != "images":
            continue

        if not filename.lower().endswith(
            (".jpg", ".jpeg", ".png")
        ):
            continue

        # Tao ma SHA256 tu noi dung anh
        image_data = z.read(name)

        image_hash = hashlib.sha256(
            image_data
        ).hexdigest()

        hashes[image_hash].append(
            (split, filename)
        )

        total_images += 1

# Tim nhom anh trung hoan toan giua cac tap
duplicates = []

for items in hashes.values():

    splits = {split for split, _ in items}

    # Chi quan tam trung giua nhieu tap
    if len(splits) > 1:
        duplicates.append(items)

# Hien thi ket qua
print("\n===== KIEM TRA ANH TRUNG =====")
print("Tong anh:", total_images)
print("Nhom anh trung giua cac tap:", len(duplicates))

# In toi da 10 nhom trung
for index, group in enumerate(duplicates[:10], 1):

    print(f"\nNhom {index}:")

    for split, filename in group:
        print(" ", split, "-", filename)

if not duplicates:
    print("\nKHONG PHAT HIEN ANH TRUNG HOAN TOAN!")
else:
    print("\nCAN KIEM TRA CAC ANH TRUNG!")

print("\nLuu y: Chua kiem tra anh gan giong nhau.")
print("Dataset goc: KHONG THAY DOI")
