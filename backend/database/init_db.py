
# Import hàm kết nối SQLite đã tạo ở bước trước
from backend.database.connection import get_connection


# Hàm khởi tạo các bảng cơ sở dữ liệu
def init_database():

    # Mở kết nối đến SQLite
    connection = get_connection()

    try:
        # Tạo bảng lưu thông tin phiên giám sát
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sessions (

                -- Mã định danh duy nhất của phiên
                session_id TEXT PRIMARY KEY,

                -- Loại nguồn video
                source_type TEXT NOT NULL
                    CHECK (source_type IN ('file', 'camera', 'rtsp')),

                -- Đường dẫn file hoặc địa chỉ nguồn video
                source TEXT NOT NULL,

                -- Trạng thái của phiên giám sát
                status TEXT NOT NULL DEFAULT 'STOPPED'
                    CHECK (status IN ('RUNNING', 'STOPPED', 'ERROR')),

                -- Thời điểm tạo phiên
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Lưu thay đổi vào cơ sở dữ liệu
        connection.commit()

        print("Da khoi tao bang sessions thanh cong!")

    finally:
        # Đóng kết nối sau khi thực hiện
        connection.close()

