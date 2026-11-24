"""PostgreSQL application entry point. Run one worker for local camera sessions."""
import logging
import time
from uuid import uuid4

import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import PROJECT_ROOT
from backend.database.postgres_connection import DatabaseNotConfigured
from backend.api.health import router as health_router
from backend.api.session_pg import router as session_router
from backend.api.video_pg import router as video_router
from backend.detection_api import router as detection_router
from backend.api.detection_history_pg import router as history_router
from backend.api.alert_pg import router as alert_router
from backend.api.evidence_pg import router as evidence_router

logger = logging.getLogger("uav.backend")
app = FastAPI(
    title="UAV Weapon Detection API",
    description="Backend quan ly phien giam sat, bang chung va canh bao. Webcam mo phong UAV.",
    version="1.1.0",
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request.state.request_id = uuid4().hex
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    logger.info("%s %s status=%s duration_ms=%.1f request_id=%s",
                request.method, request.url.path, response.status_code,
                (time.perf_counter() - started) * 1000, request.state.request_id)
    return response


async def database_unavailable(request: Request, error: Exception):
    logger.warning("Database unavailable type=%s request_id=%s",
                   type(error).__name__, getattr(request.state, "request_id", "unknown"))
    return JSONResponse(
        status_code=503,
        content={"detail": "Database unavailable. Check configuration and PostgreSQL service.",
                 "request_id": getattr(request.state, "request_id", None)},
    )


for error_type in (DatabaseNotConfigured, psycopg.OperationalError, psycopg.InterfaceError,
                   psycopg.errors.UndefinedTable, psycopg.errors.UndefinedColumn):
    app.add_exception_handler(error_type, database_unavailable)


@app.exception_handler(Exception)
async def unexpected_error(request: Request, error: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("Unhandled request error request_id=%s", request_id, exc_info=error)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. See server log.", "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )


for router in (health_router, session_router, video_router, detection_router,
               history_router, alert_router, evidence_router):
    app.include_router(router)

app.mount("/web", StaticFiles(directory=str(PROJECT_ROOT / "frontend"), html=True), name="frontend")
