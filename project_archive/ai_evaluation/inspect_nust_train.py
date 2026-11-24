
from pathlib import Path
import random
import cv2
import numpy as np

BASE = Path(__file__).resolve().parents[2]

# Anh NUST goc
IMAGES = BASE / "data/raw/knife_nust_v1/train/images"

# Nhan da chuan hoa truoc do
LABELS = BASE / "data/prepared/knife_nust_v1/labels/train"

# Noi luu ket qua tren o D
OUTPUT = BASE / "data/prepared/knife_nust_v1"
OUTPUT.mkdir(parents=True, exist_ok=True)

if not IMAGES.exists():
    raise FileNotFoundError(IMAGES)

if not LABELS.exists():
    raise FileNotFoundError(LABELS)

# Lay danh sach anh
images = sorted(
    p for p in IMAGES.iterdir()
    if p.suffix.lower() in (".jpg", ".jpeg", ".png")
)

labels = list(LABELS.glob("*.txt"))

print("===== KIEM TRA KNIFE NUST =====")
print("Tong anh Train:", len(images))
print("Tong nhan Train:", len(labels))

# Kiem tra anh va nhan theo ten file
image_names = {p.stem for p in images}
label_names = {p.stem for p in labels}

print("Anh thieu nhan:", len(image_names - label_names))
print("Nhan thieu anh:", len(label_names - image_names))

# Chon ngau nhien 30 anh de kiem tra
random.seed(99)
samples = random.sample(images, min(30, len(images)))

tiles = []

for index, path in enumerate(samples, start=1):

    # Doc anh, ho tro ten file Unicode
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)

    if img is None:
        print("Khong doc duoc:", path.name)
        continue

    h, w = img.shape[:2]

    label_path = LABELS / (path.stem + ".txt")

    if label_path.exists():
        for line in label_path.read_text(
            encoding="utf-8"
        ).splitlines():

            parts = line.split()

            if len(parts) != 5:
                continue

            cls, xc, yc, bw, bh = map(float, parts)

            x1 = int((xc - bw / 2) * w)
            y1 = int((yc - bh / 2) * h)
            x2 = int((xc + bw / 2) * w)
            y2 = int((yc + bh / 2) * h)

            cv2.rectangle(
                img, (x1, y1), (x2, y2),
                (0, 255, 0), 2
            )

    img = cv2.resize(img, (200, 150))

    tile = np.full((175, 200, 3), 245, np.uint8)
    tile[:150] = img

    cv2.putText(
        tile,
        f"NUST {index:02d}",
        (8, 168),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 0),
        1
    )

    tiles.append(tile)

# Ghep 5 anh moi hang
if tiles:
    while len(tiles) % 5 != 0:
        tiles.append(
            np.full((175, 200, 3), 255, np.uint8)
        )

    rows = [
        np.hstack(tiles[i:i + 5])
        for i in range(0, len(tiles), 5)
    ]

    preview = np.vstack(rows)

    save_path = OUTPUT / "nust_train_review_99.jpg"
    cv2.imwrite(str(save_path), preview)

    print("Anh xem truoc:", save_path)

print("\nHOAN THANH KIEM TRA NUST!")
