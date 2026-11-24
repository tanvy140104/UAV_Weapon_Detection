
from pathlib import Path
from shutil import copy2

# Thu muc du an
BASE = Path(__file__).resolve().parents[2]

# Nhan da chuan hoa
LABELS = BASE / "data/prepared/knife_nust_v1/labels"

# Thu muc sao luu nhan truoc khi sua
BACKUP = BASE / "data/prepared/knife_nust_v1/backup_labels"

fixed = 0
total_boxes = 0

# Kiem tra va sua cac nhan co sai so nho
for file in LABELS.glob("*/*.txt"):

    lines = file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    changed = False

    for line in lines:

        if not line.strip():
            continue

        parts = line.split()

        # Moi nhan phai co 5 gia tri
        if len(parts) != 5 or parts[0] != "0":
            raise ValueError(f"Nhan khong hop le: {file}")

        x, y, w, h = map(float, parts[1:])

        # Tinh 4 canh khung bao
        xmin = x - w / 2
        xmax = x + w / 2
        ymin = y - h / 2
        ymax = y + h / 2

        # Kiem tra khung bao co vuot bien khong
        invalid = (
            xmin < 0 or ymin < 0 or
            xmax > 1 or ymax > 1
        )

        if invalid:

            # Chi chap nhan sai so rat nho
            eps = 0.000001

            if (
                xmin < -eps or ymin < -eps or
                xmax > 1 + eps or ymax > 1 + eps
            ):
                raise ValueError(
                    f"Khung bao sai qua lon: {file.name}"
                )

            # Dua cac canh vao ben trong anh mot chut
            margin = 0.0000001

            xmin = max(margin, xmin)
            ymin = max(margin, ymin)
            xmax = min(1 - margin, xmax)
            ymax = min(1 - margin, ymax)

            # Tinh lai toa do YOLO
            x = (xmin + xmax) / 2
            y = (ymin + ymax) / 2
            w = xmax - xmin
            h = ymax - ymin

            line = (
                f"0 {x:.12f} {y:.12f} "
                f"{w:.12f} {h:.12f}"
            )

            changed = True
            fixed += 1

        new_lines.append(line)
        total_boxes += 1

    # Chi ghi lai nhung file can sua
    if changed:

        # Sao luu file cu tren o D
        backup_file = BACKUP / file.parent.parent.name / file.name
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        if not backup_file.exists():
            copy2(file, backup_file)

        # Luu nhan da sua
        file.write_text(
            "\n".join(new_lines) + "\n",
            encoding="utf-8"
        )

        print("Da sua:", file.name)

# Kiem tra lai tat ca nhan
invalid_count = 0

for file in LABELS.glob("*/*.txt"):

    for line in file.read_text(encoding="utf-8").splitlines():

        if not line.strip():
            continue

        parts = line.split()

        if len(parts) != 5:
            invalid_count += 1
            continue

        try:
            x, y, w, h = map(float, parts[1:])

            valid = (
                parts[0] == "0" and
                w > 0 and h > 0 and
                0 <= x - w/2 and x + w/2 <= 1 and
                0 <= y - h/2 and y + h/2 <= 1
            )

            if not valid:
                invalid_count += 1

        except ValueError:
            invalid_count += 1

print("\n===== KET QUA =====")
print("Tong doi tuong:", total_boxes)
print("Nhan vua sua:", fixed)
print("Nhan con loi:", invalid_count)
print("Dataset goc: KHONG THAY DOI")
