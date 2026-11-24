from datetime import datetime
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from backend.services.detection_history_service_pg import detection_history_service_pg as history_service

router = APIRouter(prefix="/api/history", tags=["Detection History"])


@router.get("")
def get_detection_history(
    session_id: str | None = Query(default=None, max_length=100),
    label: Literal["knife", "stick", "gun"] | None = None,
    alert_status: Literal["NEW", "CONFIRMED", "FALSE_POSITIVE"] | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    try:
        return history_service.get_history_page(
            session_id=session_id, label=label, alert_status=alert_status,
            date_from=date_from, date_to=date_to, limit=limit, offset=offset,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/sessions/{session_id}")
def get_session_detection_history(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    result = history_service.get_history_page(session_id=session_id, limit=limit, offset=offset)
    return {**result, "session_id": session_id}
