
from pathlib import Path
import cv2
import numpy as np

BASE = Path(__file__).resolve().parents[2]

IMAGES = BASE / "data/field_samples/knife/original"
LABELS = BASE / "data/field_samples/manual_labels/knife"

OUTPUT = BASE / "data/field_samples/review"
OUTPUT.mkdir(parents=True, exist_ok=True)

files = sorted(IMAGES.glob("*.jpg"))

errors = []
tiles = []
total_boxes = 0

print("===== KIEM TRA NHAN YOLO =====")

for index, image_path in enumerate(files, start=1):

    image = cv2.imread(str(image_path))
    label_path = LABELS / (image_path.stem + ".txt")

    if image is None:
        errors.append(f"Khong doc duoc: {image_path.name}")
        continue

    h, w = image.shape[:2]

    if not label_path.exists():
        errors.append(f"Thieu nhan: {image_path.name}")
        lines = []
    else:
        lines = label_path.read_text(
            encoding="utf-8"
        ).splitlines()

    boxes_in_image = 0

    for line_number, line in enumerate(lines, start=1):

        parts = line.strip().split()

        if len(parts) != 5:
            errors.append(
                f"Sai dinh dang: {label_path.name}, "
                f"dong {line_number}"
            )
            continue

        try:
            class_id = int(parts[0])
            xc, yc, bw, bh = map(float, parts[1:])
        except ValueError:
            errors.append(
                f"Sai gia tri: {label_path.name}"
            )
            continue

        x1 = xc - bw / 2
        y1 = yc - bh / 2
        x2 = xc + bw / 2
        y2 = yc + bh / 2

        valid = (
            class_id == 0
            and bw > 0
            and bh > 0
            and x1 >= -0.00001
            and y1 >= -0.00001
            and x2 <= 1.00001
            and y2 <= 1.00001
        )

        if not valid:
            errors.append(
                f"Nhãn khong hop le: {label_path.name}"
            )
            continue

        p1 = (
            int(max(0, x1) * w),
            int(max(0, y1) * h)
        )

        p2 = (
            int(min(1, x2) * w),
            int(min(1, y2) * h)
        )

        cv2.rectangle(
            image, p1, p2, (0, 255, 0), 3
        )

        boxes_in_image += 1
        total_boxes += 1

    if boxes_in_image == 0:
        errors.append(
            f"Khong co khung hop le: {image_path.name}"
        )

    # Tao anh nho co khung bao
    thumb = cv2.resize(image, (240, 180))

    tile = np.full(
        (210, 240, 3), 245, dtype=np.uint8
    )

    tile[:180] = thumb

    text = f"{index:02d} | Boxes: {boxes_in_image}"

    cv2.putText(
        tile,
        text,
        (8, 201),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 0),
        1
    )

    tiles.append(tile)

# Ghep bang anh, moi hang 5 anh
columns = 5

while len(tiles) % columns:
    tiles.append(
        np.full((210, 240, 3), 255, dtype=np.uint8)
    )

if tiles:
    rows = []

    for i in range(0, len(tiles), columns):
        rows.append(np.hstack(tiles[i:i + columns]))

    preview = np.vstack(rows)

    save_path = OUTPUT / "knife_labels_checked.jpg"
    cv2.imwrite(str(save_path), preview)

    print("Anh kiem tra:", save_path)

# Kiem tra file nhan thua
image_stems = {p.stem for p in files}
label_stems = {p.stem for p in LABELS.glob("*.txt")}

extra = label_stems - image_stems

for stem in sorted(extra):
    errors.append(f"Nhan khong co anh: {stem}")

print("\n===== KET QUA =====")
print("Tong anh:", len(files))
print("Tong khung dao:", total_boxes)
print("So loi:", len(errors))

for err in errors:
    print("LOI:", err)

if not errors:
    print("NHAN YOLO HOP LE!")
    print("CAN KIEM TRA BANG ANH TRUC QUAN.")
