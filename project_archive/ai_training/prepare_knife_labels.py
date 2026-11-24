
from pathlib import Path
import math

# Thu muc goc du an
BASE = Path(__file__).resolve().parents[2]

# Dataset goc - KHONG thay doi
SRC = BASE / "data" / "raw" / "knife_nust_v1"

# Noi luu nhan da chuan hoa
DST = BASE / "data" / "prepared" / "knife_nust_v1"

total_files = 0
total_boxes = 0
converted = 0

# Duyet 3 tap du lieu
for split in ["train", "valid", "test"]:

    src_labels = SRC / split / "labels"
    dst_labels = DST / "labels" / split

    # Tao thu muc luu nhan moi
    dst_labels.mkdir(parents=True, exist_ok=True)

    # Duyet tung file nhan
    for label_file in src_labels.glob("*.txt"):

        new_lines = []

        content = label_file.read_text(
            encoding="utf-8-sig"
        )

        for line in content.splitlines():

            parts = line.strip().split()

            if not parts:
                continue

            # Dataset nay chi co lop knife = 0
            if parts[0] != "0":
                raise ValueError(
                    f"Sai class: {label_file.name}"
                )

            # Truong hop 1: Bounding Box binh thuong
            if len(parts) == 5:

                new_lines.append(" ".join(parts))

            # Truong hop 2: Polygon nhieu diem
            elif len(parts) >= 7 and len(parts) % 2 == 1:

                # Lay tat ca toa do polygon
                coords = [float(x) for x in parts[1:]]

                # Kiem tra toa do hop le
                if not all(
                    math.isfinite(v) and 0 <= v <= 1
                    for v in coords
                ):
                    raise ValueError(
                        f"Toa do loi: {label_file.name}"
                    )

                # Tach toa do X va Y
                xs = coords[0::2]
                ys = coords[1::2]

                # Tim gioi han khung bao
                x_min = min(xs)
                x_max = max(xs)
                y_min = min(ys)
                y_max = max(ys)

                # Chuyen sang dinh dang YOLO Detection
                x_center = (x_min + x_max) / 2
                y_center = (y_min + y_max) / 2
                width = x_max - x_min
                height = y_max - y_min

                if width <= 0 or height <= 0:
                    raise ValueError(
                        f"Khung bao loi: {label_file.name}"
                    )

                # Tao dong nhan moi
                new_line = (
                    f"0 {x_center:.8f} "
                    f"{y_center:.8f} "
                    f"{width:.8f} "
                    f"{height:.8f}"
                )

                new_lines.append(new_line)
                converted += 1

            else:
                raise ValueError(
                    f"Dinh dang nhan la: {label_file.name}"
                )

            total_boxes += 1

        # Ghi nhan da chuan hoa sang thu muc moi
        output_file = dst_labels / label_file.name

        output_file.write_text(
            "\n".join(new_lines) + (
                "\n" if new_lines else ""
            ),
            encoding="utf-8"
        )

        total_files += 1

    print(f"Da xu ly tap {split}")

# Thong ke ket qua
print("\n===== KET QUA CHUAN HOA =====")
print("Tong file nhan:", total_files)
print("Tong doi tuong:", total_boxes)
print("Polygon da chuyen:", converted)
print("Thu muc:", DST)
print("Dataset goc: KHONG THAY DOI")
