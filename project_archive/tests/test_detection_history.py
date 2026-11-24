
# ==========================================
# BUOC 9.9D - TEST LUU LICH SU NHAN DIEN
# ==========================================

from uuid import uuid4

from backend.database.connection import get_connection

from backend.services.detection_history_service import (
    detection_history_service
)


def main():

    # ======================================
    # 1. TAO SESSION TEST RIENG
    # ======================================

    test_session_id = "TEST_" + uuid4().hex

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO sessions (
                session_id,
                source_type,
                source,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                test_session_id,
                "file",
                "data/videos/test.mp4",
                "STOPPED"
            )
        )

        conn.commit()

    finally:
        conn.close()

    print("===== BAT DAU KIEM THU =====")
    print("Session test:", test_session_id)

    try:

        # ==================================
        # 2. TAO DU LIEU DAO GIA LAP
        # ==================================

        knife_detection = {
            "label": "knife",
            "confidence": 0.6505,
            "bbox": {
                "x1": 200.0,
                "y1": 116.4,
                "x2": 457.4,
                "y2": 478.8
            }
        }

        # ==================================
        # 3. TEST LUU LAN DAU
        # ==================================

        print("\nTEST 1 - LUU DAO LAN DAU")

        result1 = (
            detection_history_service.save_detections(
                test_session_id,
                [knife_detection]
            )
        )

        print(result1)

        assert result1["saved"] == 1
        assert result1["skipped"] == 0

        # ==================================
        # 4. TEST CHONG LUU TRUNG
        # ==================================

        print("\nTEST 2 - LUU LAI DAO NGAY LAP TUC")

        result2 = (
            detection_history_service.save_detections(
                test_session_id,
                [knife_detection]
            )
        )

        print(result2)

        assert result2["saved"] == 0
        assert result2["skipped"] == 1

        # ==================================
        # 5. TEST LUU NHAN KHAC
        # ==================================

        stick_detection = {
            "label": "stick",
            "confidence": 0.79,
            "bbox": {
                "x1": 100.0,
                "y1": 80.0,
                "x2": 180.0,
                "y2": 450.0
            }
        }

        print("\nTEST 3 - LUU THEM GAY")

        result3 = (
            detection_history_service.save_detections(
                test_session_id,
                [stick_detection]
            )
        )

        print(result3)

        assert result3["saved"] == 1

        # ==================================
        # 6. KIEM TRA LICH SU
        # ==================================

        history = (
            detection_history_service.get_history(
                session_id=test_session_id
            )
        )

        print("\n===== LICH SU TRONG DATABASE =====")

        for record in history:

            print(
                "ID:", record["detection_id"],
                "| Label:", record["label"],
                "| Confidence:", record["confidence"],
                "| Status:", record["alert_status"]
            )

        assert len(history) == 2

        labels = {
            record["label"]
            for record in history
        }

        assert labels == {"knife", "stick"}

        print("\n===== KET QUA =====")
        print("So ban ghi test:", len(history))
        print("Chong trung 5 giay: THANH CONG")
        print("Luu hai nhan khac nhau: THANH CONG")
        print("DOC/GHI SQLITE THANH CONG!")

    finally:

        # ==================================
        # 7. DON DEP DU LIEU TEST
        # ==================================

        conn = get_connection()

        try:

            # Xoa phat hien cua session test
            conn.execute(
                """
                DELETE FROM detections
                WHERE session_id = ?
                """,
                (test_session_id,)
            )

            # Xoa session test
            conn.execute(
                """
                DELETE FROM sessions
                WHERE session_id = ?
                """,
                (test_session_id,)
            )

            conn.commit()

            print("\nDA DON DEP SESSION TEST!")
            print("DU LIEU PHIEN GIAM SAT CU DUOC GIU NGUYEN!")

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()


if __name__ == "__main__":
    main()
