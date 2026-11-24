
import cv2

# Mở webcam mặc định trên laptop Windows
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Kiểm tra camera
if not cap.isOpened():
    print("Khong the mo camera!")
    raise SystemExit(1)

print("Camera da ket noi thanh cong!")
print("Nhan Q de thoat.")

try:
    while True:
        # Đọc khung hình từ webcam
        ret, frame = cap.read()

        if not ret:
            print("Khong doc duoc khung hinh!")
            break

        # Hiển thị hình ảnh trực tiếp
        cv2.imshow("UAV Weapon Detection - Laptop Camera", frame)

        # Nhấn Q để kết thúc
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    # Giải phóng camera và đóng cửa sổ
    cap.release()
    cv2.destroyAllWindows()

print("Da dong camera!")
