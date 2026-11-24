
# ==========================================
# ALERT SERVICE
# CAP NHAT TRANG THAI CANH BAO
# ==========================================

from backend.database.connection import get_connection


class AlertService:

    def __init__(self):

        # Cac trang thai duoc phep
        self.valid_statuses = {
            "NEW",
            "CONFIRMED",
            "FALSE_POSITIVE"
        }

    # ======================================
    # 1. CAP NHAT TRANG THAI CANH BAO
    # ======================================

    def update_alert_status(
        self,
        detection_id: int,
        alert_status: str
    ):

        # Kiem tra ID
        if (
            not isinstance(detection_id, int)
            or isinstance(detection_id, bool)
            or detection_id <= 0
        ):
            raise ValueError(
                "Detection ID khong hop le"
            )

        # Kiem tra trang thai
        if alert_status not in self.valid_statuses:
            raise ValueError(
                "Trang thai canh bao khong hop le"
            )

        conn = get_connection()

        try:

            # Kiem tra ban ghi ton tai
            detection = conn.execute(
                """
                SELECT detection_id
                FROM detections
                WHERE detection_id = ?
                """,
                (detection_id,)
            ).fetchone()

            if detection is None:
                raise LookupError(
                    "Khong tim thay ban ghi nhan dien"
                )

            # Cap nhat trang thai
            conn.execute(
                """
                UPDATE detections
                SET alert_status = ?
                WHERE detection_id = ?
                """,
                (
                    alert_status,
                    detection_id
                )
            )

            conn.commit()

            # Lay du lieu moi sau khi cap nhat
            updated = conn.execute(
                """
                SELECT *
                FROM detections
                WHERE detection_id = ?
                """,
                (detection_id,)
            ).fetchone()

            return dict(updated)

        except Exception:

            conn.rollback()
            raise

        finally:

            conn.close()


# ==========================================
# DOI TUONG DUNG CHUNG
# ==========================================

alert_service = AlertService()
