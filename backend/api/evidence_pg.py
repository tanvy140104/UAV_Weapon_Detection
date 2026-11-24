
# ==========================================
# EVIDENCE API - POSTGRESQL
# UAV WEAPON DETECTION
# ==========================================

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    status
)

from fastapi.responses import FileResponse

from backend.database.postgres_connection import (
    get_pg_connection
)

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
# 2. API LAY ANH BANG CHUNG
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
    # 3. DOC DUONG DAN ANH TU POSTGRESQL
    # ======================================

    with get_pg_connection() as conn:

        detection = conn.execute(
            """
            SELECT
                detection_id,
                snapshot_path
            FROM detections
            WHERE detection_id = %s
            """,
            (detection_id,)
        ).fetchone()

    # Khong tim thay ban ghi
    if detection is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )

    # Ban ghi chua co anh bang chung
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


# ==========================================
# 6. KIEM TRA ANH BANG CHUNG
# CHI DOC DU LIEU, KHONG SUA DATABASE
# ==========================================

if __name__ == "__main__":

    import os
    import getpass

    os.environ["UAV_PG_PASSWORD"] = (
        getpass.getpass(
            "Mat khau uav_backend: "
        )
    )

    print("\n===== TEST EVIDENCE POSTGRESQL =====")

    # Lay ban ghi moi nhat co duong dan anh
    with get_pg_connection() as conn:

        detection = conn.execute(
            """
            SELECT
                detection_id,
                snapshot_path
            FROM detections
            WHERE snapshot_path IS NOT NULL
              AND snapshot_path <> ''
            ORDER BY detection_id DESC
            LIMIT 1
            """
        ).fetchone()

    if detection is None:

        print("Chua co anh bang chung trong Database")

    else:

        detection_id = detection["detection_id"]

        print("Detection ID:", detection_id)

        print(
            "Snapshot path:",
            detection["snapshot_path"]
        )

        try:

            # Goi truc tiep ham API de kiem tra
            response = get_evidence_image(
                detection_id=detection_id
            )

            print("Tim ban ghi: PASS")
            print("Tim file anh: PASS")
            print("Media type:", response.media_type)
            print("File:", response.path)

        except HTTPException as error:

            print(
                "EVIDENCE ERROR:",
                error.detail
            )

            raise

    print("\nEVIDENCE POSTGRESQL: READY")
