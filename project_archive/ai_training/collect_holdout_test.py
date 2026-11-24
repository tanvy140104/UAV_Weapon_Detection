
import cv2
from pathlib import Path
from datetime import datetime

# ========================================
# 1. THU MUC DU AN
# ========================================

BASE = Path(__file__).resolve().parents[2]

OUTPUT = (
    BASE / "data"
    / "field_eval_holdout_v1"
)

KNIFE_DIR = OUTPUT / "knife"
NORMAL_DIR = OUTPUT / "normal"

KNIFE_DIR.mkdir(parents=True, exist_ok=True)
NORMAL_DIR.mkdir(parents=True, exist_ok=True)

# ========================================
# 2. MO WEBCAM
# ========================================

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    raise RuntimeError("Khong mo duoc webcam!")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("\n===== THU THAP ANH KIEM THU MOI =====")
print("K: Luu anh co dao")
print("N: Luu anh khong co vu khi")
print("Q hoac ESC: Thoat")
print("\nKhong su dung lai anh da train!")

knife_count = 0
normal_count = 0

# ========================================
# 3. THU THAP ANH
# ========================================

try:
    while True:
        ok, frame = cap.read()

        if not ok:
            print("Loi doc webcam!")
            break

        # Anh hien thi co chu huong dan
        preview = frame.copy()

        cv2.putText(
            preview,
            "K: Knife | N: Normal | Q: Quit",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2
        )

        cv2.putText(
            preview,
            f"Knife: {knife_count} | Normal: {normal_count}",
            (10, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2
        )

        cv2.imshow("Holdout Test Collection", preview)

        key = cv2.waitKey(1) & 0xFF

        # Ten file khong bi trung
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        if key == ord("k"):
            path = KNIFE_DIR / f"knife_{timestamp}.jpg"

            cv2.imwrite(
                str(path),
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 95]
            )

            knife_count += 1
            print(f"Da luu KNIFE {knife_count}: {path.name}")

        elif key == ord("n"):
            path = NORMAL_DIR / f"normal_{timestamp}.jpg"

            cv2.imwrite(
                str(path),
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 95]
            )

            normal_count += 1
            print(f"Da luu NORMAL {normal_count}: {path.name}")

        elif key in [ord("q"), 27]:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()

# ========================================
# 4. THONG KE
# ========================================

print("\n===== KET QUA THU THAP =====")
print("Anh dao:", knife_count)
print("Anh normal:", normal_count)
print("Tong anh moi:", knife_count + normal_count)
print("Thu muc:", OUTPUT)

print("\nKHONG DUOC THEM TAP NAY VAO TRAIN!")
print("HOAN THANH!")
