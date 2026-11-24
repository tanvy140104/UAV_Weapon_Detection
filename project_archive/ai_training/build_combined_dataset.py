
from pathlib import Path

# ==========================================
# 1. KHAI BAO THU MUC DU AN
# ==========================================

# Thu muc goc du an tren o D
BASE = Path(__file__).resolve().parents[2]

# Dataset GKS da huan luyen
GKS = BASE / "data" / "weapons_gks_v1"

# Dataset webcam da chuan bi
FIELD = BASE / "data" / "prepared" / "field_webcam_v1"

# Noi luu cau hinh dataset ket hop
OUTPUT = BASE / "data" / "combined_gks_field_v1"
OUTPUT.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. HAM DOC DANH SACH ANH
# ==========================================

def get_images(folder):

    if not folder.is_dir():
        raise FileNotFoundError(folder)

    return sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    )


# ==========================================
# 3. HAM KIEM TRA ANH VA NHAN YOLO
# ==========================================

def check_labels(images):

    for image in images:

        # Vi du:
        # data/weapons_gks_v1/images/train/gks_00008.jpg
        #
        # Duong dan nhan dung:
        # data/weapons_gks_v1/labels/train/gks_00008.txt

        # Quay ve thu muc goc cua dataset
        dataset_root = image.parent.parent.parent

        # Tao duong dan file nhan
        label = (
            dataset_root
            / "labels"
            / image.parent.name
            / (image.stem + ".txt")
        )

        if not label.is_file():
            raise FileNotFoundError(
                f"Khong tim thay nhan: {label}"
            )


# ==========================================
# 4. DOC DU LIEU GKS
# ==========================================

gks_train = get_images(GKS / "images" / "train")
gks_valid = get_images(GKS / "images" / "valid")
gks_test = get_images(GKS / "images" / "test")

# Doc 60 anh webcam
field_train = get_images(FIELD / "images" / "train")

print("===== KIEM TRA DU LIEU BAN DAU =====")
print("GKS Train:", len(gks_train))
print("GKS Valid:", len(gks_valid))
print("GKS Test:", len(gks_test))
print("Webcam Train:", len(field_train))


# ==========================================
# 5. KIEM TRA SO LUONG ANH
# ==========================================

if len(gks_train) != 7052:
    raise RuntimeError("So anh GKS Train khong dung!")

if len(gks_valid) != 975:
    raise RuntimeError("So anh GKS Valid khong dung!")

if len(gks_test) != 980:
    raise RuntimeError("So anh GKS Test khong dung!")

if len(field_train) != 60:
    raise RuntimeError("So anh Webcam khong dung!")


# ==========================================
# 6. KIEM TRA FILE NHAN
# ==========================================

print("\nDang kiem tra nhan GKS Train...")
check_labels(gks_train)

print("Dang kiem tra nhan GKS Valid...")
check_labels(gks_valid)

print("Dang kiem tra nhan GKS Test...")
check_labels(gks_test)

print("Dang kiem tra nhan Webcam...")
check_labels(field_train)

print("Tat ca anh deu co file nhan!")


# ==========================================
# 7. KIEM TRA ANH BINH THUONG
# ==========================================

# Anh normal khong co vu khi
# Nen file nhan phai rong

normal_count = 0
knife_count = 0

for image in field_train:

    label = (
        FIELD
        / "labels"
        / "train"
        / (image.stem + ".txt")
    )

    if image.stem.startswith("field_normal_"):

        normal_count += 1

        if label.read_text(
            encoding="utf-8"
        ).strip():

            raise ValueError(
                f"Anh normal co nhan: {image.name}"
            )

    elif image.stem.startswith("field_knife_"):

        knife_count += 1

        lines = [
            line.strip()
            for line in label.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        if len(lines) != 1:
            raise ValueError(
                f"Anh dao khong co dung 1 khung: {image.name}"
            )

        parts = lines[0].split()

        if len(parts) != 5 or parts[0] != "0":
            raise ValueError(
                f"Nhan dao khong hop le: {image.name}"
            )

    else:
        raise ValueError(
            f"Ten anh webcam khong hop le: {image.name}"
        )

if knife_count != 33 or normal_count != 27:
    raise RuntimeError(
        "So anh dao/normal khong dung!"
    )

print("Knife Webcam:", knife_count)
print("Normal Webcam:", normal_count)


# ==========================================
# 8. KET HOP DANH SACH ANH TRAIN
# ==========================================

# Khong sao chep anh
# Chi ghep danh sach duong dan

train_images = gks_train + field_train

# File danh sach anh Train
TRAIN_LIST = OUTPUT / "train_images.txt"

# Ghi duong dan Windows tuyet doi
# De Ultralytics tim dung images va labels
TRAIN_LIST.write_text(
    "\n".join(
        str(image.resolve())
        for image in train_images
    ) + "\n",
    encoding="utf-8"
)


# ==========================================
# 9. TAO FILE DATA.YAML
# ==========================================

YAML = OUTPUT / "data.yaml"

yaml_text = (
    f"path: {BASE.as_posix()}\n"
    f"train: {TRAIN_LIST.as_posix()}\n"
    f"val: {(GKS / 'images' / 'valid').as_posix()}\n"
    f"test: {(GKS / 'images' / 'test').as_posix()}\n"
    "\n"
    "names:\n"
    "  0: knife\n"
    "  1: stick\n"
    "  2: gun\n"
)

YAML.write_text(
    yaml_text,
    encoding="utf-8"
)


# ==========================================
# 10. IN KET QUA
# ==========================================

print("\n===== DATASET KET HOP =====")
print("GKS Train:", len(gks_train))
print("Webcam Train:", len(field_train))
print("Tong Train:", len(train_images))
print("Validation:", len(gks_valid))
print("Test:", len(gks_test))
print("So lop: 3")

print("\nTrain list:", TRAIN_LIST)
print("YAML:", YAML)

print("\nKHONG SAO CHEP ANH GKS")
print("KHONG THAY DOI DATASET GOC")
print("TAO CAU HINH DATASET THANH CONG!")
