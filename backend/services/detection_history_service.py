
# ==========================================
# DETECTION HISTORY SERVICE
# Luu lich su nhan dien vao SQLite
# ==========================================

import math

from backend.database.connection import get_connection


class DetectionHistoryService:

    def __init__(self):

        # Moi loai vu khi chi luu toi da
        # 1 lan trong 5 giay cua cung session
        self.cooldown_seconds = 5

        # Cac nhan YOLO duoc phep luu
        self.valid_labels = {
            "knife",
            "stick",
            "gun"
        }

    # ======================================
    # 1. KIEM TRA DU LIEU NHAN DIEN
    # ======================================

    def validate_detection(self, detection):

        if not isinstance(detection, dict):
            raise ValueError(
                "Detection phai la dictionary"
            )

        label = detection.get("label")

        if label not in self.valid_labels:
            raise ValueError(
                f"Nhan khong hop le: {label}"
            )

        confidence = float(
            detection["confidence"]
        )

        if (
            not math.isfinite(confidence)
            or confidence < 0
            or confidence > 1
        ):
            raise ValueError(
                "Confidence phai nam trong [0, 1]"
            )

        bbox = detection["bbox"]

        x1 = float(bbox["x1"])
        y1 = float(bbox["y1"])
        x2 = float(bbox["x2"])
        y2 = float(bbox["y2"])

        coordinates = [x1, y1, x2, y2]

        if not all(
            math.isfinite(value)
            for value in coordinates
        ):
            raise ValueError(
                "Toa do bbox khong hop le"
            )

        if (
            x1 < 0
            or y1 < 0
            or x2 <= x1
            or y2 <= y1
        ):
            raise ValueError(
                "Kich thuoc bbox khong hop le"
            )

        return {
            "label": label,
            "confidence": confidence,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        }

    # ======================================
    # 2. LUU DANH SACH NHAN DIEN
    # ======================================

    def save_detections(
        self,
        session_id,
        detections
    ):

        if not isinstance(session_id, str):
            raise ValueError(
                "Session ID khong hop le"
            )

        session_id = session_id.strip()

        if not session_id:
            raise ValueError(
                "Session ID khong duoc rong"
            )

        if not isinstance(detections, list):
            raise ValueError(
                "Detections phai la list"
            )

        # Khong co vu khi thi khong ghi DB
        if not detections:
            return {
                "saved": 0,
                "skipped": 0,
                "detection_ids": []
            }

        # Kiem tra du lieu truoc khi ghi
        valid_detections = [
            self.validate_detection(item)
            for item in detections
        ]

        saved = 0
        skipped = 0
        detection_ids = []

        conn = get_connection()

        try:

            # Khoa ghi de tranh hai luong
            # dong thoi tao ban ghi trung
            conn.execute("BEGIN IMMEDIATE")

            # Kiem tra session ton tai
            session = conn.execute(
                """
                SELECT session_id
                FROM sessions
                WHERE session_id = ?
                """,
                (session_id,)
            ).fetchone()

            if session is None:
                raise LookupError(
                    "Session khong ton tai"
                )

            for item in valid_detections:

                label = item["label"]

                # ==========================
                # 3. CHONG LUU TRUNG
                # ==========================

                # Tim phat hien cung nhan
                # trong 5 giay gan nhat
                recent = conn.execute(
                    """
                    SELECT detection_id
                    FROM detections
                    WHERE session_id = ?
                      AND label = ?
                      AND detected_at >=
                          datetime('now', ?)
                    LIMIT 1
                    """,
                    (
                        session_id,
                        label,
                        f"-{self.cooldown_seconds} seconds"
                    )
                ).fetchone()

                if recent is not None:

                    skipped += 1
                    continue

                # ==========================
                # 4. GHI VAO SQLITE
                # ==========================

                cursor = conn.execute(
                    """
                    INSERT INTO detections (
                        session_id,
                        label,
                        confidence,
                        x1,
                        y1,
                        x2,
                        y2,
                        alert_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'NEW')
                    """,
                    (
                        session_id,
                        label,
                        item["confidence"],
                        item["x1"],
                        item["y1"],
                        item["x2"],
                        item["y2"]
                    )
                )

                detection_ids.append(
                    cursor.lastrowid
                )

                saved += 1

            # Luu transaction
            conn.commit()

            return {
                "saved": saved,
                "skipped": skipped,
                "detection_ids": detection_ids
            }

        except Exception:

            # Co loi thi huy thay doi
            conn.rollback()
            raise

        finally:

            # Luon dong ket noi
            conn.close()

    # ======================================
    # 5. DOC LICH SU NHAN DIEN
    # ======================================

    def get_history(
        self,
        session_id=None,
        limit=50
    ):

        limit = int(limit)

        if limit < 1 or limit > 500:
            raise ValueError(
                "Limit phai tu 1 den 500"
            )

        conn = get_connection()

        try:

            if session_id is None:

                rows = conn.execute(
                    """
                    SELECT *
                    FROM detections
                    ORDER BY detection_id DESC
                    LIMIT ?
                    """,
                    (limit,)
                ).fetchall()

            else:

                rows = conn.execute(
                    """
                    SELECT *
                    FROM detections
                    WHERE session_id = ?
                    ORDER BY detection_id DESC
                    LIMIT ?
                    """,
                    (session_id, limit)
                ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:

            conn.close()


# ==========================================
# DOI TUONG DUNG CHUNG CHO BACKEND
# ==========================================

detection_history_service = (
    DetectionHistoryService()
)
