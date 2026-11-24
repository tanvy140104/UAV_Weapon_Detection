
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE / "data/field_samples"

IMAGES = ROOT / "knife/original"
LABELS = ROOT / "manual_labels/knife"
BACKUP = LABELS / "backup_before_correction"

# So thu tu anh can sua trong bang preview
FIX_INDICES = [2, 5, 7, 8, 9, 11, 12, 13, 19, 20, 25]

images = sorted(IMAGES.glob("*.jpg"))

if len(images) != 33:
    raise RuntimeError(
        f"Can kiem tra lai so anh: {len(images)}"
    )

# Kiem tra tat ca truoc khi thay doi
tasks = []

for index in FIX_INDICES:
    image = images[index - 1]
    label = LABELS / f"{image.stem}.txt"
    backup = BACKUP / label.name

    if not label.is_file():
        raise FileNotFoundError(label)

    if backup.exists():
        raise FileExistsError(backup)

    tasks.append((index, label, backup))

BACKUP.mkdir(parents=True, exist_ok=True)

# Sao luu va dua nhan cu ra khoi thu muc
for index, label, backup in tasks:
    shutil.move(str(label), str(backup))
    print(f"Anh {index:02d}: Da sao luu nhan cu")

print("\nSO ANH CAN GAN NHAN LAI:", len(tasks))
print("Nhan cu duoc giu tai:", BACKUP)
print("KHONG XOA ANH GOC")
