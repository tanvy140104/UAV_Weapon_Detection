
import cv2
import os
import random
import numpy as np

from pathlib import Path
from zipfile import ZipFile

# Thu muc du an
BASE = Path(__file__).resolve().parents[2]

# Dataset goc
ZIP_FILE = BASE / "data/Gun-Knife-Stick Detection.v5i.yolov11.zip"

# Nhan da chuan hoa 3 lop
LABELS = BASE / "data/prepared/gun_knife_stick_v5/labels"

# Anh ket qua
OUTPUT = BASE / "data/prepared/gun_knife_stick_v5/preview.jpg"

# Anh tong hop 4 hang x 4 cot
SIZE = 300
canvas = np.zeros((SIZE * 4, SIZE * 4, 3), dtype=np.uint8)

# ID goc -> ID moi
CLASS_MAP = {0: 0, 1: 2, 2: 2, 3: 1}
CLASS_NAMES = ["KNIFE", "STICK", "GUN"]

# Mau khung nhan dien (BGR)
COLORS = {
    0: (0, 255, 255),
    1: (0, 255, 0),
    2: (0, 100, 255)
}


def long_path(path):
    # Ho tro ten file dai tren Windows
    path = str(path.resolve())

    if os.name == "nt":
        return "\\\\?\\" + path

    return path


rng = random.Random(42)

with ZipFile(ZIP_FILE) as z:

    names = z.namelist()

    # Tim anh theo ten file nhan
    image_map = {}

    for name in names:
        parts = name.split("/")

        if (
            len(parts) == 3
            and parts[1] == "images"
            and name.lower().endswith((".jpg", ".jpeg", ".png"))
        ):
            image_map[(parts[0], Path(name).stem)] = name

    # Phan loai file nhan de lay mau
    groups = {0: [], 1: [], 2: []}
    polygons = []

    for name in names:

        parts = name.split("/")

        if not (
            len(parts) == 3
            and parts[1] == "labels"
            and name.endswith(".txt")
        ):
            continue

        content = z.read(name).decode("utf-8-sig")

        lines = [
            line.split()
            for line in content.splitlines()
            if line.strip()
        ]

        # Xac dinh cac lop xuat hien trong anh
        classes = {
            CLASS_MAP[int(line[0])]
            for line in lines
        }

        for cls in classes:
            groups[cls].append(name)

        # File chua nhan Polygon goc
        if any(len(line) != 5 for line in lines):
            polygons.append(name)

    # Chon 4 anh moi nhom, khong trung nhau
    selected = []
    used = set()

    sample_groups = [
        ("KNIFE", groups[0]),
        ("STICK", groups[1]),
        ("GUN", groups[2]),
        ("POLYGON", polygons)
    ]

    for title, candidates in sample_groups:

        available = [n for n in candidates if n not in used]

        if len(available) < 4:
            raise RuntimeError(
                f"Khong du anh cho nhom {title}"
            )

        chosen = rng.sample(available, 4)

        for name in chosen:
            selected.append((title, name))
            used.add(name)

    # Doc anh tu ZIP va ve nhan da chuan hoa
    for index, (title, label_name) in enumerate(selected):

        split = label_name.split("/")[0]
        stem = Path(label_name).stem

        image_name = image_map.get((split, stem))

        if image_name is None:
            raise FileNotFoundError(label_name)

        # Doc anh truc tiep tu ZIP
        image_bytes = np.frombuffer(
            z.read(image_name),
            dtype=np.uint8
        )

        image = cv2.imdecode(
            image_bytes,
            cv2.IMREAD_COLOR
        )

        if image is None:
            raise RuntimeError(image_name)

        height, width = image.shape[:2]

        # Doc file nhan da chuyen doi
        label_file = LABELS / split / (stem + ".txt")

        with open(long_path(label_file), encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:

            if not line.strip():
                continue

            cls, x, y, w, h = map(float, line.split())
            cls = int(cls)

            x1 = max(0, int((x - w / 2) * width))
            y1 = max(0, int((y - h / 2) * height))
            x2 = min(width - 1, int((x + w / 2) * width))
            y2 = min(height - 1, int((y + h / 2) * height))

            color = COLORS[cls]

            # Ve khung bao vu khi
            cv2.rectangle(
                image,
                (x1, y1),
                (x2, y2),
                color,
                3
            )

            cv2.putText(
                image,
                CLASS_NAMES[cls],
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2
            )

        # Thu nho de ghep anh
        image = cv2.resize(image, (SIZE, SIZE))

        # Tieu de cua tung anh
        cv2.rectangle(
            image, (0, 0), (SIZE, 32),
            (30, 30, 30), -1
        )

        cv2.putText(
            image,
            f"{title} - {split.upper()}",
            (8, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255, 255, 255),
            2
        )

        row = index // 4
        col = index % 4

        canvas[
            row * SIZE:(row + 1) * SIZE,
            col * SIZE:(col + 1) * SIZE
        ] = image

# Luu anh tong hop tren o D
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

if not cv2.imwrite(str(OUTPUT), canvas):
    raise RuntimeError("Khong luu duoc anh preview")

print("DA TAO ANH KIEM TRA THANH CONG!")
print("So anh:", len(selected))
print("Duong dan:", OUTPUT)
print("4 anh dao, 4 anh gay, 4 anh sung, 4 anh Polygon")
