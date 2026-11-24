
from pathlib import Path
import cv2
import numpy as np

BASE = Path(__file__).resolve().parents[2]
SOURCE = BASE / "data" / "field_samples"
OUTPUT = SOURCE / "review"

OUTPUT.mkdir(parents=True, exist_ok=True)


def make_preview(category):

    folder = SOURCE / category / "original"
    files = sorted(folder.glob("*.jpg"))

    print(f"\n{category.upper()}: {len(files)} anh")

    tiles = []
    columns = 5

    for i, path in enumerate(files, start=1):

        img = cv2.imread(str(path))

        if img is None:
            print("LOI DOC ANH:", path.name)
            continue

        # Thu nho anh de xem tong hop
        img = cv2.resize(img, (200, 150))

        # Tao o anh va dong ten
        tile = np.full(
            (175, 200, 3),
            235,
            dtype=np.uint8
        )

        tile[:150, :] = img

        cv2.putText(
            tile,
            f"{i:02d} - {path.stem[9:15]}",
            (5, 167),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 0),
            1
        )

        tiles.append(tile)

    if not tiles:
        return

    # Them o trong cho du so cot
    while len(tiles) % columns != 0:
        tiles.append(
            np.full(
                (175, 200, 3),
                255,
                dtype=np.uint8
            )
        )

    rows = []

    for i in range(0, len(tiles), columns):
        rows.append(
            np.hstack(tiles[i:i + columns])
        )

    preview = np.vstack(rows)

    save_path = OUTPUT / f"{category}_preview.jpg"

    cv2.imwrite(str(save_path), preview)

    print("Da tao:", save_path)


make_preview("knife")
make_preview("normal")

print("\nHOAN THANH KIEM TRA ANH!")
