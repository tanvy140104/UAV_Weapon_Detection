
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from collections import Counter, defaultdict
import hashlib
import random
import csv

# Thu muc du an
BASE = Path(__file__).resolve().parents[2]

ZIP_FILE = BASE / "data/Gun-Knife-Stick Detection.v5i.yolov11.zip"

OUTPUT = BASE / "data/prepared/gun_knife_stick_v5/split_plan.csv"

# Ty le chia du lieu
RATIOS = {
    "train": 0.80,
    "valid": 0.10,
    "test": 0.10
}

# ID goc -> ID moi
CLASS_MAP = {
    0: 0,  # Knife
    1: 2,  # Pistol -> Gun
    2: 2,  # Rifle -> Gun
    3: 1   # Stick-Rod -> Stick
}

# Cau truc gom anh trung
parent = {}


def find(x):
    if x not in parent:
        parent[x] = x

    if parent[x] != x:
        parent[x] = find(parent[x])

    return parent[x]


def union(a, b):
    ra = find(a)
    rb = find(b)

    if ra != rb:
        parent[rb] = ra


records = []
total_classes = Counter()

# Doc anh va nhan tu ZIP goc
with ZipFile(ZIP_FILE) as z:

    zip_names = set(z.namelist())

    for image_name in z.namelist():

        parts = image_name.split("/")

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

        stem = PurePosixPath(filename).stem

        # Bo phan ma Roboflow de lay ten anh goc
        source_name = stem.split(".rf.")[0].lower()

        # Hash noi dung anh de tim anh trung hoan toan
        image_hash = hashlib.sha256(
            z.read(image_name)
        ).hexdigest()

        # Ghep nhom theo ten goc VA noi dung trung
        union("source:" + source_name, "hash:" + image_hash)

        # Tim nhan cua anh
        label_name = f"{split}/labels/{stem}.txt"

        if label_name not in zip_names:
            raise FileNotFoundError(label_name)

        # Dem so doi tuong theo 3 lop moi
        classes = Counter()

        content = z.read(label_name).decode("utf-8-sig")

        for line in content.splitlines():

            if not line.strip():
                continue

            old_id = int(line.split()[0])
            new_id = CLASS_MAP[old_id]

            classes[new_id] += 1
            total_classes[new_id] += 1

        records.append({
            "image": image_name,
            "label": label_name,
            "original_split": split,
            "source": source_name,
            "hash": image_hash,
            "classes": classes
        })

print("Da doc:", len(records), "anh")

# Tao cac nhom anh khong duoc tach roi
groups = defaultdict(list)

for record in records:
    group_id = find("source:" + record["source"])
    groups[group_id].append(record)

print("So nhom sau khi gom:", len(groups))

# Chia theo nhom, co can nhac so anh va so nhan
total_images = len(records)

targets = {
    s: total_images * ratio
    for s, ratio in RATIOS.items()
}

image_counts = Counter()

class_counts = {
    s: Counter() for s in RATIOS
}

# Xao tron co dinh de co the tai lap ket qua
rng = random.Random(42)

group_list = list(groups.values())
rng.shuffle(group_list)

# Xu ly nhom lon truoc
group_list.sort(key=len, reverse=True)


def split_score(choice, group_size, group_classes):

    # Sai lech so anh so voi muc tieu
    score = 0.0

    for s in RATIOS:

        value = image_counts[s]

        if s == choice:
            value += group_size

        score += ((value - targets[s]) / targets[s]) ** 2

    # Sai lech phan bo 3 lop
    class_score = 0.0

    for s in RATIOS:
        for cls in (0, 1, 2):

            value = class_counts[s][cls]

            if s == choice:
                value += group_classes[cls]

            target = max(
                1,
                total_classes[cls] * RATIOS[s]
            )

            class_score += ((value - target) / target) ** 2

    return score + 0.35 * class_score / 3


# Phan bo tung nhom
for group in group_list:

    group_classes = Counter()

    for record in group:
        group_classes.update(record["classes"])

    chosen = min(
        RATIOS,
        key=lambda s: split_score(
            s, len(group), group_classes
        )
    )

    for record in group:
        record["new_split"] = chosen

    image_counts[chosen] += len(group)
    class_counts[chosen].update(group_classes)

# Kiem tra ten goc va hash khong bi chia cheo
sources = defaultdict(set)
hashes = defaultdict(set)

for record in records:
    sources[record["source"]].add(record["new_split"])
    hashes[record["hash"]].add(record["new_split"])

source_leaks = sum(len(v) > 1 for v in sources.values())
hash_leaks = sum(len(v) > 1 for v in hashes.values())

if source_leaks or hash_leaks:
    raise RuntimeError("Van con trung anh giua cac tap!")

# Luu ke hoach vao file CSV
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w", newline="", encoding="utf-8-sig"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "image_zip_path",
        "label_zip_path",
        "original_split",
        "new_split",
        "source_name",
        "sha256"
    ])

    for record in records:
        writer.writerow([
            record["image"],
            record["label"],
            record["original_split"],
            record["new_split"],
            record["source"],
            record["hash"]
        ])

print("\n===== KE HOACH CHIA DU LIEU =====")

for split in RATIOS:
    print(
        split.upper(),
        "| Images:", image_counts[split],
        "| Knife:", class_counts[split][0],
        "| Stick:", class_counts[split][1],
        "| Gun:", class_counts[split][2]
    )

print("\nTrung ten goc giua cac tap:", source_leaks)
print("Trung SHA256 giua cac tap:", hash_leaks)

print("\nDa luu ke hoach:", OUTPUT)
print("CHUA SAO CHEP ANH - DATASET GOC GIU NGUYEN")
