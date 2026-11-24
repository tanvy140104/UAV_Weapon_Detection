
from pathlib import Path
import random

# ==========================================
# 1. CAU HINH
# ==========================================

BASE = Path(__file__).resolve().parents[2]

GKS = BASE / "data" / "weapons_gks_v1"

FIELD = BASE / "data" / "prepared" / "field_webcam_v1"

OLD_LIST = (
    BASE / "data" /
    "combined_gks_field_v1" /
    "train_images.txt"
)

OUTPUT = (
    BASE / "data" /
    "combined_gks_field_finetune"
)

OUTPUT.mkdir(parents=True, exist_ok=True)

# So lan su dung moi anh webcam
REPEAT_FIELD = 5

# ==========================================
# 2. DOC DANH SACH ANH
# ==========================================

images = [
    line.strip()
    for line in OLD_LIST.read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip()
]

field_folder = (FIELD / "images" / "train").resolve()

gks_images = []
field_images = []

for image in images:
    path = Path(image).resolve()

    if not path.is_file():
        raise FileNotFoundError(path)

    if path.parent == field_folder:
        field_images.append(str(path))
    else:
        gks_images.append(str(path))

# Kiem tra du lieu goc
assert len(gks_images) == 7052
assert len(field_images) == 60

# ==========================================
# 3. TANG TY TRONG ANH WEBCAM
# ==========================================

train_images = (
    gks_images +
    field_images * REPEAT_FIELD
)

# Tron thu tu anh de huan luyen
random.Random(42).shuffle(train_images)

# Chi ghi danh sach duong dan
TRAIN_LIST = OUTPUT / "train_images.txt"

TRAIN_LIST.write_text(
    "\n".join(train_images) + "\n",
    encoding="utf-8"
)

# ==========================================
# 4. TAO DATA.YAML MOI
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
# 5. IN KET QUA
# ==========================================

print("\n===== DATASET FINE-TUNE =====")
print("GKS:", len(gks_images))
print("Webcam goc:", len(field_images))
print("So lan lap webcam:", REPEAT_FIELD)
print("Webcam sau khi lap:",
      len(field_images) * REPEAT_FIELD)
print("Tong luot anh Train:", len(train_images))
print("Anh duy nhat:", len(set(train_images)))
print("Validation:", 975)
print("Test:", 980)

print("\nTrain list:", TRAIN_LIST)
print("Data YAML:", YAML)

print("\nKHONG COPY THEM ANH!")
print("CHUAN BI FINE-TUNE THANH CONG!")
