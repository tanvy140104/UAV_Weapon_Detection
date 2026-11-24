
# ==========================================
# BUOC 9.9B - TAO BANG DETECTIONS
# ==========================================

from backend.database.connection import (
    get_connection,
    DB_PATH
)


def main():

    # Ket noi SQLite hien tai tren o D
    conn = get_connection()

    try:

        # Dem so phien truoc khi tao bang
        sessions_before = conn.execute(
            "SELECT COUNT(*) FROM sessions"
        ).fetchone()[0]

        # ==================================
        # 1. TAO BANG LUU LICH SU NHAN DIEN
        # ==================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS detections (

                detection_id INTEGER PRIMARY KEY
                    AUTOINCREMENT,

                session_id TEXT NOT NULL,

                label TEXT NOT NULL
                    CHECK (
                        label IN ('knife', 'stick', 'gun')
                    ),

                confidence REAL NOT NULL
                    CHECK (
                        confidence >= 0
                        AND confidence <= 1
                    ),

                x1 REAL NOT NULL,
                y1 REAL NOT NULL,
                x2 REAL NOT NULL,
                y2 REAL NOT NULL,

                detected_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                alert_status TEXT NOT NULL
                    DEFAULT 'NEW'
                    CHECK (
                        alert_status IN (
                            'NEW',
                            'CONFIRMED',
                            'FALSE_POSITIVE'
                        )
                    ),

                FOREIGN KEY (session_id)
                    REFERENCES sessions(session_id)
                    ON DELETE RESTRICT
            )
        """)

        # ==================================
        # 2. TAO INDEX TIM KIEM LICH SU
        # ==================================

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_detections_session_time
            ON detections (
                session_id,
                detected_at
            )
        """)

        # Luu thay doi
        conn.commit()

        # ==================================
        # 3. KIEM TRA CAU TRUC BANG
        # ==================================

        print("===== DATABASE =====")
        print(DB_PATH)

        print("\n===== CAC BANG =====")

        tables = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        for row in tables:
            print(row["name"])

        print("\n===== BANG DETECTIONS =====")

        columns = conn.execute(
            "PRAGMA table_info(detections)"
        ).fetchall()

        for column in columns:
            print(
                column["name"],
                "-",
                column["type"]
            )

        # ==================================
        # 4. KIEM TRA KHOA NGOAI
        # ==================================

        print("\n===== KHOA NGOAI =====")

        foreign_keys = conn.execute(
            "PRAGMA foreign_key_list(detections)"
        ).fetchall()

        for fk in foreign_keys:
            print(
                fk["table"],
                ":",
                fk["from"],
                "->",
                fk["to"]
            )

        # ==================================
        # 5. KIEM TRA DU LIEU CU
        # ==================================

        sessions_after = conn.execute(
            "SELECT COUNT(*) FROM sessions"
        ).fetchone()[0]

        detections_count = conn.execute(
            "SELECT COUNT(*) FROM detections"
        ).fetchone()[0]

        print("\n===== KIEM TRA DU LIEU =====")
        print("Sessions truoc:", sessions_before)
        print("Sessions sau:", sessions_after)
        print("Detections:", detections_count)

        if sessions_before != sessions_after:
            raise RuntimeError(
                "So luong session bi thay doi!"
            )

        if not foreign_keys:
            raise RuntimeError(
                "Bang detections chua co khoa ngoai!"
            )

        print("\nTAO BANG DETECTIONS THANH CONG!")
        print("DU LIEU SESSIONS CU DUOC GIU NGUYEN!")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
