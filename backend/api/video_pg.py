# Session state is persisted in PostgreSQL
from backend.services.session_service_pg import session_service_pg as session_service
# Import công cụ xây dựng API và xử lý lỗi HTTP
from fastapi import APIRouter, HTTPException, status

# Response dùng để trả ảnh JPEG tĩnh
from fastapi.responses import Response

# StreamingResponse dùng để truyền dữ liệu liên tục
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from backend.services.video_service_pg import MonitorBusy

# Import Service xử lý video
from backend.services.video_service_pg import video_service


# Tạo nhóm API quản lý video
router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)


# API 1: Lấy thông tin kỹ thuật của video
@router.get("/info")
def get_video_info():

    try:
        # Gọi VideoService để kiểm tra nguồn video
        video_info = video_service.get_video_info()

        # Trả dữ liệu JSON cho Client
        return video_info

    except FileNotFoundError:
        # Không tìm thấy video
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )

    except RuntimeError:
        # Video bị lỗi hoặc không giải mã được
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Video cannot be opened or decoded"
        )


# API 2: Lấy khung hình đầu tiên dạng JPEG
@router.get(
    "/frame",
    responses={
        200: {
            "content": {"image/jpeg": {}},
            "description": "Khung hinh JPEG tu video"
        }
    }
)
def get_video_frame():

    try:
        # Đọc và mã hóa frame đầu tiên thành JPEG
        image_bytes = video_service.get_first_frame_jpeg()

        # Trả ảnh JPEG về trình duyệt
        return Response(
            content=image_bytes,
            media_type="image/jpeg",
            headers={"Cache-Control": "no-store"}
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )

    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot extract frame from video"
        )


# API 3: Truyền liên tục các frame theo chuẩn MJPEG
@router.get("/stream")
def stream_video():

    try:
        # Kiểm tra video tồn tại và đọc được
        # trước khi bắt đầu truyền dữ liệu
        video_service.get_video_info()

    except FileNotFoundError:
        # Trả 404 khi không tìm thấy video
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )

    except RuntimeError:
        # Trả 422 khi video không đọc được
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Video cannot be opened or decoded"
        )

    # Lấy bộ sinh dữ liệu video từ VideoService
    video_generator = video_service.generate_video_stream()

    # Truyền liên tục các ảnh JPEG qua HTTP
    return StreamingResponse(
        content=video_generator,
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-store"
        }
    )



# API 4: Xem trước video theo mã phiên giám sát
@router.get("/sessions/{session_id}/preview")
def preview_session_video(session_id: str):

    try:
        # Kiểm tra phiên có tồn tại và video có đọc được không
        # VideoService sẽ truy vấn PostgreSQL theo session_id
        source = video_service.get_capture_source(session_id)
        video_service.assert_monitor_available(session_id, source)
        video_service.get_video_info(session_id)

    except MonitorBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    except LookupError:
        # Không tìm thấy phiên giám sát
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    except ValueError as error:
        # Loại nguồn hoặc đường dẫn video không hợp lệ
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except FileNotFoundError:
        # Phiên tồn tại nhưng file video không tồn tại
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )

    except RuntimeError:
        # Video tồn tại nhưng không thể đọc được
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Video cannot be opened or decoded"
        )

    # Tạo luồng MJPEG theo nguồn video của session_id
    video_generator = video_service.generate_video_stream(
        session_id
    )

    # Trả luồng video về trình duyệt qua HTTP
    return StreamingResponse(
        content=video_generator,
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-store"
        }
    )



# API 5: One monitor owns a session and its camera until disconnect/stop.
@router.get("/sessions/{session_id}/monitor")
def monitor_session_video(session_id: str):
    session = session_service.get_session_config(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] != "RUNNING":
        raise HTTPException(status_code=409, detail="Session must be RUNNING to monitor video")
    token = None
    try:
        token = video_service.reserve_monitor(session_id)
        video_service.get_video_info(session_id)
    except MonitorBusy as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (LookupError, ValueError, RuntimeError, OSError) as error:
        if token:
            video_service.release_monitor(session_id, token)
        session_service.mark_stream_error(session_id)
        if isinstance(error, FileNotFoundError):
            code = 404
        elif isinstance(error, ValueError):
            code = 400
        elif isinstance(error, LookupError):
            code = 404
        else:
            code = 422
        raise HTTPException(status_code=code, detail=str(error)) from error
    except Exception:
        if token:
            video_service.release_monitor(session_id, token)
        raise
    return StreamingResponse(
        video_service.generate_monitoring_stream(session_id, token),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store"},
        background=BackgroundTask(video_service.release_monitor, session_id, token, finish=True),
    )
