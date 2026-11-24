
from pathlib import Path
import shutil

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# Du lieu webcam da thu thap
SOURCE = BASE / "data" / "field_samples"

# Dataset webcam moi
OUTPUT = BASE / "data" / "prepared" / "field_webcam_v1"

IMAGE_OUT = OUTPUT / "images" / "train"
LABEL_OUT = OUTPUT / "labels" / "train"

# Khong ghi de dataset da tao
if OUTPUT.exists() and any(OUTPUT.iterdir()):
    raise RuntimeError(
        f"Thu muc da co du lieu: {OUTPUT}"
    )

knife_images = sorted(
    (SOURCE / "knife" / "original").glob("*.jpg")
)

normal_images = sorted(
    (SOURCE / "normal" / "original").glob("*.jpg")
)

print("===== KIEM TRA ANH WEBCAM =====")
print("Knife:", len(knife_images))
print("Normal:", len(normal_images))

if len(knife_images) != 33:
    raise RuntimeError("So anh dao khong dung 33!")

if len(normal_images) != 27:
    raise RuntimeError("So anh normal khong dung 27!")

# Kiem tra nhan dao truoc khi sao chep
for image in knife_images:
    label = (
        SOURCE / "manual_labels" / "knife" /
        (image.stem + ".txt")
    )

    if not label.is_file():
        raise FileNotFoundError(label)

    lines = [
        line.strip()
        for line in label.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    if len(lines) != 1:
        raise ValueError(
            f"Anh phai co dung 1 khung dao: {image.name}"
        )

    parts = lines[0].split()

    if len(parts) != 5 or parts[0] != "0":
        raise ValueError(
            f"Nhan YOLO khong hop le: {label}"
        )

# Tao thu muc tren o D
IMAGE_OUT.mkdir(parents=True, exist_ok=True)
LABEL_OUT.mkdir(parents=True, exist_ok=True)

# Sao chep 33 anh dao va nhan
for i, image in enumerate(knife_images, start=1):

    new_name = f"field_knife_{i:03d}"

    shutil.copy2(
        image,
        IMAGE_OUT / (new_name + ".jpg")
    )

    original_label = (
        SOURCE / "manual_labels" / "knife" /
        (image.stem + ".txt")
    )

    shutil.copy2(
        original_label,
        LABEL_OUT / (new_name + ".txt")
    )

# Sao chep 27 anh khong co vu khi
for i, image in enumerate(normal_images, start=1):

    new_name = f"field_normal_{i:03d}"

    shutil.copy2(
        image,
        IMAGE_OUT / (new_name + ".jpg")
    )

    # File nhan rong: khong co doi tuong vu khi
    (LABEL_OUT / (new_name + ".txt")).write_text(
        "",
        encoding="utf-8"
    )

# Kiem tra ket qua
images = list(IMAGE_OUT.glob("*.jpg"))
labels = list(LABEL_OUT.glob("*.txt"))

print("\n===== KET QUA =====")
print("Tong anh:", len(images))
print("Tong nhan:", len(labels))
print("Knife:", len(knife_images))
print("Normal:", len(normal_images))
print("Thu muc:", OUTPUT)

if len(images) == 60 and len(labels) == 60:
    print("\nCHUAN BI DATASET THANH CONG!")
