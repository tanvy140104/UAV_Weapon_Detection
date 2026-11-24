
from pathlib import Path
import cv2

# Thu muc du an tren o D
BASE = Path(__file__).resolve().parents[2]

# Anh dao da thu thap
IMAGES = BASE / "data/field_samples/knife/original"

# Noi luu nhan YOLO moi
LABELS = BASE / "data/field_samples/manual_labels/knife"
LABELS.mkdir(parents=True, exist_ok=True)

# Cac anh can gan nhan
files = sorted(IMAGES.glob("*.jpg"))

# Trang thai chuot
state = {
    "start": None,
    "current": None,
    "boxes": []
}


def mouse_callback(event, x, y, flags, userdata):

    if event == cv2.EVENT_LBUTTONDOWN:
        state["start"] = (x, y)
        state["current"] = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE:
        if state["start"] is not None:
            state["current"] = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        if state["start"] is None:
            return

        x0, y0 = state["start"]

        x1, x2 = sorted([x0, x])
        y1, y2 = sorted([y0, y])

        if x2 - x1 >= 5 and y2 - y1 >= 5:
            state["boxes"].append((x1, y1, x2, y2))

        state["start"] = None
        state["current"] = None


def save_yolo_labels(path, width, height):

    lines = []

    for x1, y1, x2, y2 in state["boxes"]:

        x1 = max(0, min(x1, width))
        x2 = max(0, min(x2, width))
        y1 = max(0, min(y1, height))
        y2 = max(0, min(y2, height))

        # Chuyen toa do pixel sang YOLO
        xc = (x1 + x2) / (2 * width)
        yc = (y1 + y2) / (2 * height)
        bw = (x2 - x1) / width
        bh = (y2 - y1) / height

        if bw > 0 and bh > 0:
            # Class 0 = knife
            lines.append(
                f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}"
            )

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )


def main():

    print("===== GAN NHAN ANH DAO =====")
    print("Tong anh:", len(files))
    print("Keo chuot trai: Ve khung dao")
    print("S: Luu va chuyen anh tiep")
    print("U: Xoa khung vua ve")
    print("R: Xoa tat ca khung")
    print("Q: Thoat va giu nhan da luu")

    window = "GKS - Label Knife"
    cv2.namedWindow(window, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(window, mouse_callback)

    for index, image_path in enumerate(files, start=1):

        label_path = LABELS / f"{image_path.stem}.txt"

        # Khong gan nhan lai anh da luu
        if label_path.exists():
            print(f"Bo qua anh da gan nhan: {index}")
            continue

        image = cv2.imread(str(image_path))

        if image is None:
            print("Khong doc duoc:", image_path)
            continue

        height, width = image.shape[:2]

        state["start"] = None
        state["current"] = None
        state["boxes"] = []

        print(f"\nAnh {index}/{len(files)}: {image_path.name}")

        while True:

            display = image.copy()

            # Ve cac khung da hoan thanh
            for x1, y1, x2, y2 in state["boxes"]:
                cv2.rectangle(
                    display,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

            # Ve khung dang keo
            if state["start"] and state["current"]:
                cv2.rectangle(
                    display,
                    state["start"],
                    state["current"],
                    (0, 255, 255),
                    2
                )

            cv2.putText(
                display,
                f"IMAGE {index}/{len(files)} | BOXES: {len(state['boxes'])}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2
            )

            cv2.imshow(window, display)

            key = cv2.waitKey(20) & 0xFF

            if key == ord("s"):

                if not state["boxes"]:
                    print("Chua ve khung! Hay ve khung dao.")
                    continue

                save_yolo_labels(
                    label_path, width, height
                )

                print("DA LUU:", label_path.name)
                break

            elif key == ord("u"):
                if state["boxes"]:
                    state["boxes"].pop()

            elif key == ord("r"):
                state["boxes"] = []

            elif key == ord("q") or key == 27:
                cv2.destroyAllWindows()
                print("Da thoat. Nhan da luu van duoc giu.")
                return

    cv2.destroyAllWindows()
    print("\nHOAN THANH GAN NHAN!")


if __name__ == "__main__":
    main()
