
# ==========================================
# DETECTION HISTORY API
# API DOC LICH SU NHAN DIEN VU KHI
# ==========================================

from fastapi import APIRouter, Query

from backend.services.detection_history_service import (
    detection_history_service
)


# Tao nhom API lich su nhan dien
router = APIRouter(
    prefix="/api/history",
    tags=["Detection History"]
)


# ==========================================
# API 1: LAY DANH SACH LICH SU NHAN DIEN
# ==========================================

@router.get("")
def get_detection_history(
    session_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=500)
):

    # Lay du lieu tu DetectionHistoryService
    history = detection_history_service.get_history(
        session_id=session_id,
        limit=limit
    )

    # Tra ve JSON cho giao dien Web
    return {
        "status": "success",
        "count": len(history),
        "detections": history
    }


# ==========================================
# API 2: LAY LICH SU THEO MA PHIEN
# ==========================================

@router.get("/sessions/{session_id}")
def get_session_detection_history(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=500)
):

    # Loc lich su theo session_id
    history = detection_history_service.get_history(
        session_id=session_id,
        limit=limit
    )

    return {
        "status": "success",
        "session_id": session_id,
        "count": len(history),
        "detections": history
    }
