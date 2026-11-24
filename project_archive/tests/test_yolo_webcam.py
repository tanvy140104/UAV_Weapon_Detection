
import cv2
from pathlib import Path
from ultralytics import YOLO

# Xac dinh thu muc goc cua du an
BASE_DIR = Path(__file__).resolve().parents[2]

# Tai mo hinh YOLO da luu tren o D
model = YOLO(str(BASE_DIR / "models" / "yolo11n.pt"))

# Mo webcam laptop tren Windows
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Kiem tra camera co hoat dong khong
if not cap.isOpened():
    print("Khong mo duoc webcam!")
    raise SystemExit(1)

print("BAT DAU NHAN DIEN DAO")
print("Nguong tin cay: 20%")
print("Kich thuoc xu ly anh: 800")
print("Nhan Q de thoat.")

try:
    while True:

        # Doc hinh anh tu webcam
        ret, frame = cap.read()

        if not ret:
            print("Khong doc duoc frame!")
            break

        # ==========================================
        # CHAY YOLO BANG GPU GTX 1650
        # ==========================================

        results = model.predict(
            frame,
            device=0,        # Su dung GPU NVIDIA
            imgsz=800,       # Tang kich thuoc anh xu ly
            classes=[43],    # Chi phat hien lop knife
            conf=0.20,       # Giam nguong tin cay xuong 20%
            verbose=False
        )

        # Ve khung nhan dien xung quanh dao
        annotated = results[0].plot()

        # Dem so dao duoc AI phat hien
        knife_count = len(results[0].boxes)

        # ==========================================
        # HIEN THI CANH BAO
        # ==========================================

        if knife_count > 0:

            # Hien thi canh bao mau do
            cv2.putText(
                annotated,
                f"WARNING: KNIFE DETECTED ({knife_count})",
                (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        else:

            # Hien thi trang thai khi khong phat hien dao
            cv2.putText(
                annotated,
                "STATUS: NO KNIFE DETECTED",
                (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        # ==========================================
        # HIEN THI VIDEO KEM KET QUA AI
        # ==========================================

        cv2.imshow(
            "UAV Weapon Detection - Knife AI",
            annotated
        )

        # Nhan Q de dong chuong trinh
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:

    # Giai phong webcam
    cap.release()

    # Dong tat ca cua so OpenCV
    cv2.destroyAllWindows()

print("Da ket thuc nhan dien!")
