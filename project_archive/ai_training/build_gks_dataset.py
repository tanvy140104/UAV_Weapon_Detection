
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from collections import Counter
import csv
import os
import shutil

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# Dataset goc
ZIP_FILE = BASE / "data/Gun-Knife-Stick Detection.v5i.yolov11.zip"

# Ke hoach chia du lieu da kiem tra
PLAN = BASE / "data/prepared/gun_knife_stick_v5/split_plan.csv"

# Nhan da chuan hoa 3 lop
LABELS = BASE / "data/prepared/gun_knife_stick_v5/labels"

# Dataset YOLO11 moi, luu tren o D
OUTPUT = BASE / "data/weapons_gks_v1"

SPLITS = ("train", "valid", "test")

# Ho tro duong dan dai tren Windows
def long_path(path):
    absolute = str(path.resolve())

    if os.name == "nt":
        return "\\\\?\\" + absolute

    return absolute


# Doc ke hoach chia du lieu
with PLAN.open(
    "r", encoding="utf-8-sig", newline=""
) as f:
    records = list(csv.DictReader(f))

if len(records) != 9007:
    raise ValueError(
        f"So anh khong dung: {len(records)}"
    )

# Tranh ghi de dataset da tao truoc do
if OUTPUT.exists() and any(OUTPUT.iterdir()):
    raise RuntimeError(
        f"Thu muc dich da co du lieu: {OUTPUT}"
    )

# Tao thu muc anh va nhan
for split in SPLITS:
    (OUTPUT / "images" / split).mkdir(
        parents=True, exist_ok=True
    )

    (OUTPUT / "labels" / split).mkdir(
        parents=True, exist_ok=True
    )

counts = Counter()

# Doc anh truc tiep tu ZIP
with ZipFile(ZIP_FILE) as z:

    zip_names = set(z.namelist())

    for index, row in enumerate(records, start=1):

        image_name = row["image_zip_path"]
        old_label = row["label_zip_path"]
        old_split = row["original_split"]
        new_split = row["new_split"]

        if old_split not in SPLITS:
            raise ValueError(old_split)

        if new_split not in SPLITS:
            raise ValueError(new_split)

        if image_name not in zip_names:
            raise FileNotFoundError(image_name)

        # Lay dinh dang anh goc
        extension = PurePosixPath(
            image_name
        ).suffix.lower()

        if extension not in (".jpg", ".jpeg", ".png"):
            raise ValueError(image_name)

        # Tao ten ngan, duy nhat
        short_name = f"gks_{index:05d}"

        image_out = (
            OUTPUT / "images" / new_split /
            (short_name + extension)
        )

        label_out = (
            OUTPUT / "labels" / new_split /
            (short_name + ".txt")
        )

        # Doc nhan 3 lop da chuan hoa
        label_filename = PurePosixPath(
            old_label
        ).name

        label_source = (
            LABELS / old_split / label_filename
        )

        # Doc nhan truoc khi ghi anh
        with open(
            long_path(label_source),
            "rb"
        ) as f:
            label_data = f.read()

        # Ghi anh voi ten ngan
        with z.open(image_name) as src:
            with image_out.open("wb") as dst:
                shutil.copyfileobj(src, dst)

        # Ghi nhan tuong ung
        label_out.write_bytes(label_data)

        counts[new_split] += 1

        if index % 1000 == 0:
            print(
                f"Da xu ly {index}/{len(records)} anh"
            )

# Tao file cau hinh YOLO
yaml_file = OUTPUT / "data.yaml"

yaml_content = (
    f"path: {OUTPUT.as_posix()}\n"
    "train: images/train\n"
    "val: images/valid\n"
    "test: images/test\n"
    "\n"
    "names:\n"
    "  0: knife\n"
    "  1: stick\n"
    "  2: gun\n"
)

yaml_file.write_text(
    yaml_content,
    encoding="utf-8"
)

# In ket qua
print("\n===== DATASET YOLO11 =====")

for split in SPLITS:
    print(
        split.upper(),
        ":", counts[split], "anh"
    )

print("TONG:", sum(counts.values()))
print("SO LOP: 3")
print("FILE YAML:", yaml_file)
print("THU MUC:", OUTPUT)
print("DATASET GOC: KHONG THAY DOI")

if sum(counts.values()) == 9007:
    print("\nTAO DATASET THANH CONG!")
