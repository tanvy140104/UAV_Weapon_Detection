
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import math
import os

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# File ZIP dataset goc - KHONG THAY DOI
SOURCE = BASE / "data" / "Gun-Knife-Stick Detection.v5i.yolov11.zip"

# Thu muc chua nhan da chuan hoa
OUTPUT = BASE / "data" / "prepared" / "gun_knife_stick_v5" / "labels"

# Chuyen 4 lop goc thanh 3 lop
# 0 Knife     -> 0 knife
# 1 Pistol    -> 2 gun
# 2 Rifle     -> 2 gun
# 3 Stick-Rod -> 1 stick
CLASS_MAP = {
    0: 0,
    1: 2,
    2: 2,
    3: 1
}

# Gioi han sai so toa do
EPS = 1e-6
MARGIN = 1e-7

total_files = 0
total_boxes = 0
converted_polygons = 0

class_counts = Counter()
split_counts = Counter()


def windows_long_path(path):
    # Ho tro duong dan dai tren Windows
    absolute = str(path.resolve())

    if os.name == "nt":
        return "\\\\?\\" + absolute

    return absolute


def normalize_box(xmin, ymin, xmax, ymax):
    # Kiem tra toa do co phai so hop le
    values = [xmin, ymin, xmax, ymax]

    if not all(math.isfinite(v) for v in values):
        raise ValueError("Toa do khong phai so huu han")

    # Khong chap nhan toa do vuot bien qua lon
    if (
        xmin < -EPS or ymin < -EPS
        or xmax > 1 + EPS or ymax > 1 + EPS
    ):
        raise ValueError("Khung bao vuot ngoai anh")

    # Gioi han vao trong anh, tranh sai so lam tron
    xmin = max(MARGIN, min(1 - MARGIN, xmin))
    ymin = max(MARGIN, min(1 - MARGIN, ymin))
    xmax = max(MARGIN, min(1 - MARGIN, xmax))
    ymax = max(MARGIN, min(1 - MARGIN, ymax))

    if xmax <= xmin or ymax <= ymin:
        raise ValueError("Khung bao co kich thuoc khong hop le")

    # Chuyen sang toa do YOLO Detection
    x = (xmin + xmax) / 2
    y = (ymin + ymax) / 2
    w = xmax - xmin
    h = ymax - ymin

    return x, y, w, h


# Doc truc tiep tu ZIP de tranh loi ten file qua dai
with ZipFile(SOURCE, "r") as z:

    files = [
        n for n in z.namelist()
        if (
            n.endswith(".txt")
            and len(n.split("/")) == 3
            and n.split("/")[0] in ("train", "valid", "test")
            and n.split("/")[1] == "labels"
        )
    ]

    for name in files:

        split, _, filename = name.split("/")

        # Doc file nhan goc
        content = z.read(name).decode("utf-8-sig")

        new_lines = []

        for line in content.splitlines():

            parts = line.strip().split()

            if not parts:
                continue

            # Doc ID lop
            old_class = int(parts[0])

            if old_class not in CLASS_MAP:
                raise ValueError(f"Class ID khong hop le: {name}")

            new_class = CLASS_MAP[old_class]

            coords = [float(v) for v in parts[1:]]

            if not all(math.isfinite(v) for v in coords):
                raise ValueError(f"Toa do khong hop le: {name}")

            # Truong hop 1: Bounding Box - 5 gia tri
            if len(parts) == 5:

                x, y, w, h = coords

                if w <= 0 or h <= 0:
                    raise ValueError(f"Kich thuoc khong hop le: {name}")

                xmin = x - w / 2
                ymin = y - h / 2
                xmax = x + w / 2
                ymax = y + h / 2

            # Truong hop 2: Polygon - nhieu cap toa do
            elif len(parts) >= 7 and len(parts) % 2 == 1:

                xs = coords[0::2]
                ys = coords[1::2]

                xmin = min(xs)
                ymin = min(ys)
                xmax = max(xs)
                ymax = max(ys)

                converted_polygons += 1

            else:
                raise ValueError(f"Dinh dang nhan la: {name}")

            # Chuan hoa va kiem tra khung bao
            x, y, w, h = normalize_box(
                xmin, ymin, xmax, ymax
            )

            # Tao nhan YOLO voi ID moi
            new_lines.append(
                f"{new_class} {x:.12f} {y:.12f} "
                f"{w:.12f} {h:.12f}"
            )

            total_boxes += 1
            class_counts[new_class] += 1

        # Ghi file moi, khong sua file goc
        output_file = OUTPUT / split / filename

        # Ho tro duong dan dai tren Windows
        output_folder = windows_long_path(output_file.parent)
        os.makedirs(output_folder, exist_ok=True)

        with open(
            windows_long_path(output_file),
            "w",
            encoding="utf-8"
        ) as f:
            if new_lines:
                f.write("\n".join(new_lines) + "\n")

        total_files += 1
        split_counts[split] += 1

    # In ket qua
    print("\n===== KET QUA CHUAN HOA =====")
    print("Tong file nhan:", total_files)
    print("Tong doi tuong:", total_boxes)
    print("Polygon da chuyen:", converted_polygons)

    print("\nSo file theo tap:")
    for split in ["train", "valid", "test"]:
        print(split, ":", split_counts[split])

    print("\nSo doi tuong theo lop moi:")
    print("0 - knife:", class_counts[0])
    print("1 - stick:", class_counts[1])
    print("2 - gun:", class_counts[2])

    print("\nThu muc luu nhan:", OUTPUT)
    print("Dataset goc: KHONG THAY DOI")
