from backend.services.video_service_pg import video_service, MonitorBusy
# Import công cụ tạo API và xử lý lỗi HTTP
from fastapi import APIRouter, HTTPException, Query, status

# Import cấu trúc dữ liệu đầu vào và đầu ra
from backend.schemas.session import (
    SessionStartRequest,
    SessionResponse
)

# Import Service xử lý nghiệp vụ
from backend.services.session_service_pg import session_service_pg as session_service


# Tạo Router quản lý phiên giám sát
router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)


# API 1: Tạo phiên giám sát mới
@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_session(request: SessionStartRequest):

    # Gọi Service để tạo và lưu phiên vào PostgreSQL
    new_session = session_service.create_session(request)

    # Trả thông tin phiên vừa tạo cho Client
    return new_session


# API 2: Lấy danh sách tất cả phiên giám sát
@router.get(
    "",
    response_model=list[SessionResponse]
)
def get_all_sessions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):

    # Gọi Service đọc danh sách phiên từ PostgreSQL
    sessions = session_service.get_all_sessions(limit=limit, offset=offset)

    # Trả danh sách dưới dạng JSON
    return sessions


# API 3: Lấy thông tin một phiên theo session_id
@router.get(
    "/{session_id}",
    response_model=SessionResponse
)
def get_session(session_id: str):

    # Gọi Service tìm phiên theo mã ID
    session = session_service.get_session(session_id)

    # Trả lỗi 404 nếu không tìm thấy phiên
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Trả thông tin phiên đã tìm thấy
    return session


# API 4: Kích hoạt trạng thái phiên giám sát
@router.post(
    "/{session_id}/start",
    response_model=SessionResponse
)
def start_session(session_id: str):

    # Bước 1: Kiểm tra phiên có tồn tại trong PostgreSQL
    session = session_service.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Bước 2: Kiểm tra trạng thái hiện tại
    if session.status != "STOPPED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session must be STOPPED before starting"
        )

    # Bước 3: Kiểm tra nguồn video của phiên
    try:
        # VideoService đọc nguồn được lưu trong PostgreSQL
        # và xác nhận có thể mở, giải mã video
        source = video_service.get_capture_source(session_id)
        video_service.assert_monitor_available(session_id, source)
        video_service.get_video_info(session_id)

    except MonitorBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Video cannot be opened or decoded"
        )

    # Bước 4: Chuyển trạng thái trong PostgreSQL
    try:
        updated_session = session_service.update_session_status(
            session_id,
            "RUNNING"
        )

    except ValueError as error:
        # Tránh chuyển trạng thái không hợp lệ
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

    # Kiểm tra phiên có bị xóa trong lúc xử lý không
    if updated_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Bước 5: Trả kết quả cho Client
    return updated_session



# API 5: Dừng trạng thái phiên giám sát
@router.post(
    "/{session_id}/stop",
    response_model=SessionResponse
)
def stop_session(session_id: str):

    # Bước 1: Tìm phiên giám sát trong PostgreSQL
    session = session_service.get_session(session_id)

    # Nếu phiên không tồn tại thì trả lỗi 404
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Bước 2: Chỉ cho phép dừng phiên đang RUNNING
    if session.status not in {"RUNNING", "ERROR"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session must be RUNNING or ERROR before stopping"
        )

    # Bước 3: Cập nhật trạng thái phiên trong PostgreSQL
    try:
        updated_session = session_service.update_session_status(
            session_id,
            "STOPPED"
        )

    except ValueError as error:
        # Trả lỗi nếu trạng thái thay đổi không hợp lệ
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

    # Kiểm tra phiên có còn tồn tại hay không
    if updated_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Bước 4: Trả trạng thái mới về cho Client
    return updated_session
