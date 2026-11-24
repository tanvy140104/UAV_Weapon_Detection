
# Tạo mã định danh duy nhất cho mỗi phiên
from uuid import uuid4

# Dùng Literal để giới hạn giá trị trạng thái
from typing import Literal

# Kết nối cơ sở dữ liệu SQLite
from backend.database.connection import get_connection

# Các Schema dữ liệu phiên giám sát
from backend.schemas.session import (
    SessionStartRequest,
    SessionResponse
)


# Lớp xử lý nghiệp vụ quản lý phiên giám sát
class SessionService:

    # 1. Tạo một phiên giám sát mới
    def create_session(
        self,
        request: SessionStartRequest
    ) -> SessionResponse:

        # Sinh mã phiên duy nhất
        session_id = str(uuid4())

        # Phiên vừa tạo mặc định chưa hoạt động
        session_status = "STOPPED"

        # Mở kết nối đến SQLite
        connection = get_connection()

        try:
            # Lưu phiên vào bảng sessions
            connection.execute(
                """
                INSERT INTO sessions (
                    session_id,
                    source_type,
                    source,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    request.source_type,
                    request.source,
                    session_status
                )
            )

            # Lưu thay đổi xuống cơ sở dữ liệu
            connection.commit()

        finally:
            # Luôn đóng kết nối
            connection.close()

        # Trả kết quả về cho API
        return SessionResponse(
            session_id=session_id,
            status=session_status,
            source_type=request.source_type
        )

    # 2. Tìm phiên theo session_id
    def get_session(
        self,
        session_id: str
    ) -> SessionResponse | None:

        connection = get_connection()

        try:
            # Lấy thông tin một phiên
            session = connection.execute(
                """
                SELECT session_id, source_type, status
                FROM sessions
                WHERE session_id = ?
                """,
                (session_id,)
            ).fetchone()

        finally:
            connection.close()

        # Không tìm thấy phiên
        if session is None:
            return None

        # Chuyển dữ liệu thành Schema
        return SessionResponse(
            session_id=session["session_id"],
            status=session["status"],
            source_type=session["source_type"]
        )

    # 3. Lấy toàn bộ danh sách phiên
    def get_all_sessions(self) -> list[SessionResponse]:

        connection = get_connection()

        try:
            # Phiên mới nhất đứng trước
            rows = connection.execute(
                """
                SELECT session_id, source_type, status
                FROM sessions
                ORDER BY created_at DESC, rowid DESC
                """
            ).fetchall()

        finally:
            connection.close()

        # Chuyển danh sách SQLite thành Schema
        sessions = [
            SessionResponse(
                session_id=row["session_id"],
                status=row["status"],
                source_type=row["source_type"]
            )
            for row in rows
        ]

        return sessions

    # 4. Lấy cấu hình nguồn video theo session_id
    def get_session_config(
        self,
        session_id: str
    ) -> dict | None:

        connection = get_connection()

        try:
            # Lấy đầy đủ thông tin nguồn video
            row = connection.execute(
                """
                SELECT
                    session_id,
                    source_type,
                    source,
                    status
                FROM sessions
                WHERE session_id = ?
                """,
                (session_id,)
            ).fetchone()

            # Phiên không tồn tại
            if row is None:
                return None

            return dict(row)

        finally:
            connection.close()

    # 5. Cập nhật trạng thái phiên giám sát
    def update_session_status(
        self,
        session_id: str,
        new_status: Literal["RUNNING", "STOPPED", "ERROR"]
    ) -> SessionResponse | None:

        # Các quy tắc chuyển trạng thái hợp lệ
        allowed_transitions = {
            "STOPPED": {"RUNNING"},
            "RUNNING": {"STOPPED", "ERROR"},
            "ERROR": {"STOPPED"}
        }

        # Kiểm tra trạng thái đầu vào
        if new_status not in allowed_transitions:
            raise ValueError("Invalid session status")

        # Mở kết nối đến SQLite
        connection = get_connection()

        try:
            # Bắt đầu giao dịch ghi để tránh cập nhật đồng thời
            connection.execute("BEGIN IMMEDIATE")

            # Lấy trạng thái hiện tại của phiên
            session = connection.execute(
                """
                SELECT session_id, source_type, status
                FROM sessions
                WHERE session_id = ?
                """,
                (session_id,)
            ).fetchone()

            # Không tìm thấy phiên
            if session is None:
                return None

            old_status = session["status"]

            # Kiểm tra có được phép chuyển trạng thái không
            if new_status not in allowed_transitions.get(
                old_status, set()
            ):
                raise ValueError(
                    f"Cannot change status from "
                    f"{old_status} to {new_status}"
                )

            # Cập nhật trạng thái trong SQLite
            connection.execute(
                """
                UPDATE sessions
                SET status = ?
                WHERE session_id = ?
                """,
                (new_status, session_id)
            )

            # Lưu trạng thái mới
            connection.commit()

            # Trả về thông tin phiên sau khi cập nhật
            return SessionResponse(
                session_id=session_id,
                status=new_status,
                source_type=session["source_type"]
            )

        except Exception:
            # Hủy thay đổi nếu gặp lỗi
            connection.rollback()
            raise

        finally:
            # Đóng kết nối
            connection.close()


# Tạo đối tượng dùng chung cho các API
session_service = SessionService()
