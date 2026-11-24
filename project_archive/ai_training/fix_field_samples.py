
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE / "data" / "field_samples"

# Cac moc thoi gian duoc xac dinh tu anh preview
PLAN = [
    ("normal", "knife", [
        "110453", "110456", "110458", "110459"
    ]),
    ("knife", "normal", [
        "110706", "110707"
    ]),
]

moves = []

# Kiem tra day du truoc khi di chuyen
for old_group, new_group, times in PLAN:
    for time_code in times:

        matches = list(
            (ROOT / old_group / "original").glob(
                f"20261123_{time_code}_*.jpg"
            )
        )

        if len(matches) != 1:
            raise RuntimeError(
                f"Khong tim thay dung 1 anh: "
                f"{old_group} - {time_code}"
            )

        filename = matches[0].name

        for subfolder in ["original", "prediction"]:
            src = ROOT / old_group / subfolder / filename
            dst = ROOT / new_group / subfolder / filename

            if not src.is_file():
                raise FileNotFoundError(src)

            if dst.exists():
                raise FileExistsError(dst)

            moves.append((src, dst))

# Chuyen ca anh goc va anh du doan
for src, dst in moves:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

print("===== KET QUA PHAN LOAI LAI =====")
print("Da chuyen 4 anh normal -> knife")
print("Da chuyen 2 anh knife -> normal")
print("Tong file da chuyen:", len(moves))

for group in ["knife", "normal"]:
    count = len(
        list((ROOT / group / "original").glob("*.jpg"))
    )
    print(f"{group.upper()}: {count} anh")

print("\nHOAN THANH!")
print("Du lieu goc va prediction da duoc dong bo.")

