
# Thư viện làm việc với đường dẫn thư mục và file
from pathlib import Path

# SQLite là cơ sở dữ liệu tích hợp sẵn trong Python
import sqlite3


# Xác định thư mục gốc của dự án
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Đường dẫn lưu file cơ sở dữ liệu SQLite
DB_PATH = PROJECT_ROOT / "data" / "uav_weapon.db"


# Hàm tạo kết nối đến cơ sở dữ liệu
def get_connection() -> sqlite3.Connection:

    # Tự động tạo thư mục data nếu chưa có
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Mở kết nối SQLite
    connection = sqlite3.connect(DB_PATH, timeout=10)

    # Cho phép truy cập dữ liệu bằng tên cột
    connection.row_factory = sqlite3.Row

    # Bật kiểm tra khóa ngoại để đảm bảo toàn vẹn dữ liệu
    connection.execute("PRAGMA foreign_keys = ON")

    # Trả về kết nối để các module khác sử dụng
    return connection
