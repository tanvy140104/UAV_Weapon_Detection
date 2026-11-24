
# ==========================================
# MAIN BACKEND - UAV WEAPON DETECTION
# ==========================================

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# API kiem tra Backend
from backend.api.health import (
    router as health_router
)

# API quan ly phien giam sat
from backend.api.session import (
    router as session_router
)

# API video MP4 va webcam
from backend.api.video import (
    router as video_router
)

# API nhan dien vu khi bang YOLO11n
from backend.detection_api import (
    router as detection_router
)

# API doc lich su nhan dien tu SQLite
from backend.api.detection_history import (
    router as detection_history_router
)

# API cap nhat trang thai canh bao
from backend.api.alert import (
    router as alert_router
)

# API xem anh bang chung - MOI
from backend.api.evidence import (
    router as evidence_router
)


# ==========================================
# 1. KHOI TAO FASTAPI
# ==========================================

app = FastAPI(
    title="UAV Weapon Detection API",
    description=(
        "Backend phat hien dao, gay, sung "
        "bang camera UAV va AI tren laptop"
    ),
    version="1.0.0"
)


# ==========================================
# 2. DANG KY CAC NHOM API
# ==========================================

# Kiem tra Backend
app.include_router(health_router)

# Quan ly phien giam sat
app.include_router(session_router)

# Video MP4 va webcam
app.include_router(video_router)

# AI nhan dien vu khi
app.include_router(detection_router)

# Lich su nhan dien
app.include_router(detection_history_router)

# Xac nhan / Danh dau nhan dien sai
app.include_router(alert_router)

# Xem anh bang chung
app.include_router(evidence_router)


# ==========================================
# 3. KET NOI GIAO DIEN WEB
# ==========================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

FRONTEND_DIR = PROJECT_ROOT / "frontend"

app.mount(
    "/web",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)
