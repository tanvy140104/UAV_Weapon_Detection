
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE / "data/field_samples"

IMAGES = ROOT / "knife/original"
LABELS = ROOT / "manual_labels/knife"
BACKUP = LABELS / "backup_final_correction"

# 4 anh can sua
FIX = [5, 8, 9, 25]

images = sorted(IMAGES.glob("*.jpg"))
tasks = []

for index in FIX:
    image = images[index - 1]
    label = LABELS / f"{image.stem}.txt"
    backup = BACKUP / label.name

    if not label.exists():
        raise FileNotFoundError(label)

    if backup.exists():
        raise FileExistsError(backup)

    tasks.append((index, label, backup))

BACKUP.mkdir(parents=True, exist_ok=True)

for index, label, backup in tasks:
    shutil.move(str(label), str(backup))
    print(f"Anh {index:02d}: Da sao luu nhan cu")

print("\nDa chuan bi sua 4 anh.")
print("Khong xoa anh goc.")
