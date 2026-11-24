import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg

from backend.database.postgres_connection import DatabaseNotConfigured, get_pg_connection

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check():
    return {"status": "ok", "message": "UAV Weapon Detection Backend is running"}


@router.get("/health/ready", responses={503: {"description": "Dependency unavailable"}})
def readiness_check():
    from backend.services.detection_service import MODEL_PATH
    database_ready = False
    try:
        with get_pg_connection() as conn:
            conn.execute("SELECT session_id, last_error FROM sessions LIMIT 0")
            conn.execute("SELECT detection_id, snapshot_path FROM detections LIMIT 0")
        database_ready = True
    except (DatabaseNotConfigured, psycopg.Error):
        logger.warning("Database readiness check failed")
    model_ready = MODEL_PATH.is_file()
    ready = database_ready and model_ready
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready",
                 "database": "ready" if database_ready else "unavailable",
                 "model": "present" if model_ready else "missing"},
    )
