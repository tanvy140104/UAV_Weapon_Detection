
# ==========================================
# EVIDENCE API - XEM ANH BANG CHUNG
# ==========================================

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    status
)

from fastapi.responses import FileResponse

# Ket noi Database SQLite
from backend.database.connection import get_connection

# Dich vu quan ly anh bang chung
from backend.services.evidence_service import (
    evidence_service
)


# ==========================================
# 1. KHAI BAO ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/evidence",
    tags=["Evidence"]
)


# ==========================================
# 2. API LAY ANH THEO MA PHAT HIEN
# ==========================================

@router.get(
    "/{detection_id}/image",
    responses={
        200: {
            "content": {
                "image/jpeg": {}
            },
            "description": "Anh bang chung JPEG"
        }
    }
)
def get_evidence_image(
    detection_id: int = Path(
        ...,
        gt=0,
        description="Ma ban ghi phat hien"
    )
):

    # ======================================
    # 3. TIM ANH TRONG SQLITE
    # ======================================

    conn = get_connection()

    try:

        detection = conn.execute(
            """
            SELECT
                detection_id,
                snapshot_path
            FROM detections
            WHERE detection_id = ?
            """,
            (detection_id,)
        ).fetchone()

    finally:

        conn.close()

    # Khong tim thay ban ghi
    if detection is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )

    # Ban ghi cu chua co anh bang chung
    relative_path = detection["snapshot_path"]

    if not relative_path:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence image not available"
        )

    # ======================================
    # 4. KIEM TRA DUONG DAN AN TOAN
    # ======================================

    try:

        image_path = (
            evidence_service.get_snapshot_path(
                relative_path
            )
        )

    except FileNotFoundError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence image file not found"
        )

    except ValueError:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid evidence image path"
        )

    # ======================================
    # 5. TRA ANH JPEG VE TRINH DUYET
    # ======================================

    return FileResponse(
        path=str(image_path),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff"
        }
    )
