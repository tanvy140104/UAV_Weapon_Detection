
# ==========================================
# MIGRATE SQLITE TO POSTGRESQL
# UAV WEAPON DETECTION
# ==========================================

import sqlite3
import getpass

from pathlib import Path
from datetime import datetime, timezone

import psycopg


# ==========================================
# 1. DUONG DAN DU AN
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SQLITE_PATH = (
    PROJECT_ROOT / "data" / "uav_weapon.db"
)

BACKUP_DIR = (
    PROJECT_ROOT / "data" / "backups"
)


# ==========================================
# 2. CHUYEN THOI GIAN SQLITE SANG PYTHON
# ==========================================

def parse_time(value):

    value = str(value).strip()

    value = value.replace("Z", "+00:00")

    result = datetime.fromisoformat(value)

    # Neu co timezone, chuyen ve UTC
    if result.tzinfo is not None:
        result = result.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

    return result


# ==========================================
# 3. SAO LUU SQLITE
# ==========================================

def backup_sqlite():

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup_path = (
        BACKUP_DIR
        / f"uav_weapon_before_postgres_{timestamp}.db"
    )

    source = sqlite3.connect(
        str(SQLITE_PATH)
    )

    backup = sqlite3.connect(
        str(backup_path)
    )

    try:

        source.backup(backup)

    finally:

        backup.close()
        source.close()

    print("DA SAO LUU SQLITE:")
    print(backup_path)

    return backup_path


# ==========================================
# 4. DOC DU LIEU TU BAN SAO SQLITE
# ==========================================

def read_sqlite(backup_path):

    conn = sqlite3.connect(
        str(backup_path)
    )

    conn.row_factory = sqlite3.Row

    try:

        # Kiem tra Database khong bi loi
        integrity = conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity != "ok":
            raise RuntimeError(
                "SQLite integrity check failed"
            )

        sessions = conn.execute(
            """
            SELECT *
            FROM sessions
            ORDER BY session_id
            """
        ).fetchall()

        detections = conn.execute(
            """
            SELECT *
            FROM detections
            ORDER BY detection_id
            """
        ).fetchall()

        # Chuyen Row sang dict
        sessions = [
            dict(row) for row in sessions
        ]

        detections = [
            dict(row) for row in detections
        ]

        return sessions, detections

    finally:

        conn.close()


# ==========================================
# 5. CHUYEN DU LIEU SANG POSTGRESQL
# ==========================================

def migrate(sessions, detections):

    print("\n===== SQLITE =====")
    print("Sessions:", len(sessions))
    print("Detections:", len(detections))

    # Nhap mat khau an toan
    password = getpass.getpass(
        "\nMat khau PostgreSQL uav_backend: "
    )

    # Khong hien mat khau ra Terminal
    with psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="uav_weapon_detection",
        user="uav_backend",
        password=password,
        connect_timeout=10
    ) as pg:

        with pg.cursor() as cur:

            # ==================================
            # 6. KIEM TRA POSTGRESQL CHUA CO DATA
            # ==================================

            cur.execute(
                "SELECT COUNT(*) FROM sessions"
            )

            pg_sessions_before = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM detections"
            )

            pg_detections_before = cur.fetchone()[0]

            print("\n===== POSTGRESQL TRUOC KHI CHUYEN =====")

            print(
                "Sessions:",
                pg_sessions_before
            )

            print(
                "Detections:",
                pg_detections_before
            )

            # Khong ghi de Database da co du lieu
            if (
                pg_sessions_before != 0
                or pg_detections_before != 0
            ):

                raise RuntimeError(
                    "PostgreSQL da co du lieu. "
                    "Dung de tranh ghi trung!"
                )

            # ==================================
            # 7. CHUYEN BANG SESSIONS
            # ==================================

            session_values = []

            for row in sessions:

                session_values.append((
                    row["session_id"],
                    row["source_type"],
                    row["source"],
                    row["status"],
                    parse_time(row["created_at"])
                ))

            if session_values:

                cur.executemany(
                    """
                    INSERT INTO sessions (
                        session_id,
                        source_type,
                        source,
                        status,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    session_values
                )

            print(
                "\nDA CHUYEN SESSIONS:",
                len(session_values)
            )

            # ==================================
            # 8. CHUYEN BANG DETECTIONS
            # ==================================

            detection_values = []

            for row in detections:

                detection_values.append((
                    row["detection_id"],
                    row["session_id"],
                    row["label"],
                    row["confidence"],
                    row["x1"],
                    row["y1"],
                    row["x2"],
                    row["y2"],
                    parse_time(row["detected_at"]),
                    row["alert_status"],
                    row["snapshot_path"]
                ))

            if detection_values:

                cur.executemany(
                    """
                    INSERT INTO detections (
                        detection_id,
                        session_id,
                        label,
                        confidence,
                        x1,
                        y1,
                        x2,
                        y2,
                        detected_at,
                        alert_status,
                        snapshot_path
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    """,
                    detection_values
                )

            print(
                "DA CHUYEN DETECTIONS:",
                len(detection_values)
            )

            # ==================================
            # 9. CAP NHAT BO DEM ID
            # ==================================

            # Dam bao lan INSERT tiep theo
            # khong trung detection_id cu
            cur.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence(
                        'public.detections',
                        'detection_id'
                    ),
                    COALESCE(
                        (SELECT MAX(detection_id)
                         FROM detections),
                        1
                    ),
                    (
                        SELECT COUNT(*) > 0
                        FROM detections
                    )
                )
                """
            )

            # ==================================
            # 10. KIEM TRA SO BAN GHI
            # ==================================

            cur.execute(
                "SELECT COUNT(*) FROM sessions"
            )

            pg_sessions_after = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM detections"
            )

            pg_detections_after = cur.fetchone()[0]

            if pg_sessions_after != len(sessions):
                raise RuntimeError(
                    "Sai so luong sessions!"
                )

            if pg_detections_after != len(detections):
                raise RuntimeError(
                    "Sai so luong detections!"
                )

            # ==================================
            # 11. KIEM TRA ID VA TRANG THAI
            # ==================================

            cur.execute(
                """
                SELECT
                    detection_id,
                    session_id,
                    label,
                    alert_status,
                    snapshot_path
                FROM detections
                ORDER BY detection_id
                """
            )

            pg_rows = cur.fetchall()

            sqlite_rows = [
                (
                    row["detection_id"],
                    row["session_id"],
                    row["label"],
                    row["alert_status"],
                    row["snapshot_path"]
                )
                for row in detections
            ]

            if pg_rows != sqlite_rows:
                raise RuntimeError(
                    "Du lieu detection khong khop!"
                )

            # Neu co loi truoc do,
            # transaction se tu rollback
            # va khong luu du lieu chuyen do

    # Den day transaction da commit thanh cong

    print("\n===== KET QUA =====")

    print(
        "PostgreSQL sessions:",
        pg_sessions_after
    )

    print(
        "PostgreSQL detections:",
        pg_detections_after
    )

    print("Kiem tra ID: PASS")
    print("Kiem tra trang thai: PASS")

    print("\nCHUYEN DU LIEU THANH CONG!")
    print("SQLITE CU VAN DUOC GIU NGUYEN!")


# ==========================================
# 12. CHUONG TRINH CHINH
# ==========================================

def main():

    print("===== SQLITE -> POSTGRESQL =====")

    print("Project:", PROJECT_ROOT)

    if not SQLITE_PATH.is_file():

        raise FileNotFoundError(
            f"Khong tim thay SQLite: {SQLITE_PATH}"
        )

    # Sao luu truoc khi chuyen
    backup_path = backup_sqlite()

    # Doc du lieu tu ban sao
    sessions, detections = read_sqlite(
        backup_path
    )

    # Chuyen sang PostgreSQL
    migrate(sessions, detections)


if __name__ == "__main__":
    main()
