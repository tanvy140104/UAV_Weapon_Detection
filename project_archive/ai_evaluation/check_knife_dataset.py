
import cv2
import random
import numpy as np
from pathlib import Path

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# Anh goc da giai nen
RAW = BASE / "data/raw/knife_nust_v1"

# Nhan da chuan hoa
LABELS = BASE / "data/prepared/knife_nust_v1/labels"

# Noi luu anh kiem tra
OUTPUT = BASE / "data/prepared/knife_nust_v1/preview.jpg"

# Kich thuoc tung anh hien thi
SIZE = 300

# Tao anh tong hop 3 hang, 4 cot
canvas = np.zeros((SIZE * 3, SIZE * 4, 3), dtype=np.uint8)

# Chon 3 nhan da sua de kiem tra
special = sorted(
    (LABELS / "train").glob("opencv_frame_80_png_jpg.rf.*.txt")
)[:3]

# Chon ngau nhien 9 anh tu cac tap du lieu
rng = random.Random(42)

all_labels = []
for split in ["train", "valid", "test"]:
    all_labels.extend((LABELS / split).glob("*.txt"))

remaining = [p for p in all_labels if p not in special]
samples = special + rng.sample(remaining, 12 - len(special))

# Duyet tung anh de ve khung nhan dien
for index, label_file in enumerate(samples):

    split = label_file.parent.name

    # Tim anh tuong ung voi file nhan
    image_file = None

    for ext in [".jpg", ".jpeg", ".png"]:
        candidate = (
            RAW / split / "images" /
            (label_file.stem + ext)
        )

        if candidate.exists():
            image_file = candidate
            break

    if image_file is None:
        print("Khong tim thay anh:", label_file.name)
        continue

    # Doc anh
    image = cv2.imread(str(image_file))

    if image is None:
        print("Khong doc duoc anh:", image_file.name)
        continue

    height, width = image.shape[:2]

    # Doc nhan va ve bounding box
    lines = label_file.read_text(
        encoding="utf-8"
    ).splitlines()

    for line in lines:

        if not line.strip():
            continue

        cls, x, y, w, h = map(float, line.split())

        # Chuyen toa do YOLO thanh toa do pixel
        x1 = int((x - w / 2) * width)
        y1 = int((y - h / 2) * height)
        x2 = int((x + w / 2) * width)
        y2 = int((y + h / 2) * height)

        # Ve khung mau vang quanh dao
        cv2.rectangle(
            image,
            (x1, y1),
            (x2, y2),
            (0, 255, 255),
            3
        )

    # Thu nho de ghep thanh bang 12 anh
    image = cv2.resize(image, (SIZE, SIZE))

    # Hien thi ten tap du lieu
    cv2.putText(
        image,
        f"{split.upper()} - {index + 1}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 0, 255),
        2
    )

    # Xac dinh vi tri trong bang
    row = index // 4
    col = index % 4

    canvas[
        row * SIZE:(row + 1) * SIZE,
        col * SIZE:(col + 1) * SIZE
    ] = image

# Luu anh vao o D
cv2.imwrite(str(OUTPUT), canvas)

print("DA TAO ANH KIEM TRA!")
print("Duong dan:", OUTPUT)
print("So anh duoc chon:", len(samples))

# Hien thi bang anh
cv2.imshow("Knife Dataset - Label Preview", canvas)
cv2.waitKey(0)
cv2.destroyAllWindows()
