
# ==========================================
# ALERT SERVICE - POSTGRESQL
# UAV WEAPON DETECTION
# ==========================================

from backend.database.postgres_connection import (
    get_pg_connection
)


class AlertService:

    def __init__(self):

        # Cac trang thai canh bao hop le
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

        # Kiem tra ma nhan dien
        if (
            not isinstance(detection_id, int)
            or isinstance(detection_id, bool)
            or detection_id <= 0
        ):
            raise ValueError(
                "Detection ID khong hop le"
            )

        # Kiem tra trang thai moi
        if (
            not isinstance(alert_status, str)
            or alert_status not in self.valid_statuses
        ):
            raise ValueError(
                "Trang thai canh bao khong hop le"
            )

        # Mo ket noi PostgreSQL
        # Tu commit khi thanh cong
        # Tu rollback neu xay ra loi
        with get_pg_connection() as conn:

            # UPDATE ... RETURNING:
            # Vua cap nhat, vua lay ban ghi moi
            updated = conn.execute(
                """
                UPDATE detections
                SET alert_status = %s
                WHERE detection_id = %s
                RETURNING *
                """,
                (
                    alert_status,
                    detection_id
                )
            ).fetchone()

            # Khong tim thay ma nhan dien
            if updated is None:
                raise LookupError(
                    "Khong tim thay ban ghi nhan dien"
                )

        # Chuyen ban ghi PostgreSQL thanh dict
        result = dict(updated)

        # PostgreSQL tra ve datetime
        # Chuyen sang chuoi giong PostgreSQL cu
        detected_at = result.get("detected_at")

        if detected_at is not None:
            result["detected_at"] = (
                detected_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        return result


# ==========================================
# DOI TUONG DUNG CHUNG CHO BACKEND
# ==========================================

alert_service_pg = AlertService()


# ==========================================
# 2. KIEM TRA POSTGRESQL
# CHI DOC DU LIEU, KHONG CAP NHAT
# ==========================================

if __name__ == "__main__":

    import os
    import getpass

    os.environ["UAV_PG_PASSWORD"] = (
        getpass.getpass(
            "Mat khau uav_backend: "
        )
    )

    print("\n===== TEST ALERT SERVICE =====")

    # Doc canh bao moi nhat
    with get_pg_connection() as conn:

        latest = conn.execute(
            """
            SELECT
                detection_id,
                label,
                alert_status
            FROM detections
            ORDER BY detection_id DESC
            LIMIT 1
            """
        ).fetchone()

    if latest is None:

        print("Chua co canh bao trong Database")

    else:

        print(
            "Detection ID:",
            latest["detection_id"]
        )

        print(
            "Nhan:",
            latest["label"]
        )

        print(
            "Trang thai hien tai:",
            latest["alert_status"]
        )

        print(
            "Trang thai hop le:",
            sorted(alert_service_pg.valid_statuses)
        )

    print("\nALERT SERVICE POSTGRESQL: READY")
    print("Che do kiem tra: CHI DOC DU LIEU")
