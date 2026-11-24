
# Import OpenCV để tạo và xử lý video
import cv2

# Import NumPy để tạo khung hình
import numpy as np

# Import Path để quản lý đường dẫn
from pathlib import Path


# Xác định thư mục gốc của dự án
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Đường dẫn lưu video mô phỏng
VIDEO_PATH = PROJECT_ROOT / "data" / "videos" / "test.mp4"

# Tự động tạo thư mục videos nếu chưa tồn tại
VIDEO_PATH.parent.mkdir(parents=True, exist_ok=True)


# Thiết lập thông số video
width = 640           # Chiều rộng khung hình
height = 360          # Chiều cao khung hình
fps = 15              # Số khung hình mỗi giây
duration = 10         # Thời lượng video (giây)

# Tổng số khung hình cần tạo
total_frames = fps * duration


# Chọn codec MP4
fourcc = cv2.VideoWriter_fourcc(*"mp4v")

# Tạo đối tượng ghi video
video = cv2.VideoWriter(
    str(VIDEO_PATH),
    fourcc,
    fps,
    (width, height)
)

# Kiểm tra có mở được bộ ghi video không
if not video.isOpened():
    raise RuntimeError("Khong the tao video MP4. Kiem tra codec OpenCV.")


try:
    # Tạo lần lượt từng khung hình
    for i in range(total_frames):

        # Tạo khung hình nền màu tối
        frame = np.zeros(
            (height, width, 3),
            dtype=np.uint8
        )

        # Vị trí vật thể thay đổi theo thời gian
        x = 30 + (i * 3) % 480
        y = 120

        # Vẽ hình chữ nhật chuyển động
        cv2.rectangle(
            frame,
            (x, y),
            (x + 100, y + 80),
            (0, 255, 255),
            -1
        )

        # Hiển thị tiêu đề video mô phỏng
        cv2.putText(
            frame,
            "UAV CAMERA SIMULATION",
            (65, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2
        )

        # Hiển thị số thứ tự khung hình
        cv2.putText(
            frame,
            f"Frame: {i + 1}/{total_frames}",
            (20, 330),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # Ghi khung hình vào video
        video.write(frame)

finally:
    # Đóng file video sau khi hoàn tất
    video.release()


# Thông báo kết quả
print("Da tao video mo phong!")
print("Duong dan:", VIDEO_PATH)
print("Tong so frame:", total_frames)
print("Thoi luong:", duration, "giay")
