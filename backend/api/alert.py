
# ==========================================
# ALERT API - QUAN LY TRANG THAI CANH BAO
# ==========================================

from typing import Literal

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    status
)

from pydantic import BaseModel

# Import Service cap nhat canh bao
from backend.services.alert_service import (
    alert_service
)


# ==========================================
# 1. KHAI BAO ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"]
)


# ==========================================
# 2. KHAI BAO DU LIEU GUI TU WEB
# ==========================================

class AlertStatusUpdate(BaseModel):

    # Chi chap nhan 3 trang thai hop le
    alert_status: Literal[
        "NEW",
        "CONFIRMED",
        "FALSE_POSITIVE"
    ]


# ==========================================
# 3. API CAP NHAT TRANG THAI CANH BAO
# ==========================================

@router.patch("/{detection_id}/status")
def update_alert_status(
    data: AlertStatusUpdate,

    detection_id: int = Path(
        ...,
        gt=0,
        description="Ma ban ghi nhan dien"
    )
):

    try:

        # Goi AlertService de cap nhat SQLite
        updated_detection = (
            alert_service.update_alert_status(
                detection_id=detection_id,
                alert_status=data.alert_status
            )
        )

        # Tra ket qua ve giao dien Web
        return {
            "status": "success",
            "message": (
                "Cap nhat trang thai canh bao "
                "thanh cong"
            ),
            "detection": updated_detection
        }

    except LookupError:

        # Khong tim thay ban ghi nhan dien
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )

    except ValueError as error:

        # Du lieu khong hop le
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
