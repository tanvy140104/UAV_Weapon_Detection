
# ==========================================
# BUOC 9.11A - THEM COT ANH BANG CHUNG
# ==========================================

import sqlite3

from pathlib import Path

from backend.database.connection import (
    get_connection,
    DB_PATH
)


def main():

    conn = get_connection()

    try:

        # ==================================
        # 1. SAO LUU DATABASE TRUOC KHI SUA
        # ==================================

        backup_folder = (
            DB_PATH.parent / "backups"
        )

        backup_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        backup_path = (
            backup_folder
            / "uav_weapon_before_evidence.db"
        )

        # Chi tao backup lan dau
        if not backup_path.exists():

            backup_conn = sqlite3.connect(
                backup_path
            )

            try:
                conn.backup(backup_conn)
            finally:
                backup_conn.close()

            print("DA SAO LUU DATABASE:")
            print(backup_path)

        else:

            print("DA CO BAN SAO LUU:")
            print(backup_path)

        # ==================================
        # 2. DEM BAN GHI HIEN TAI
        # ==================================

        before = conn.execute(
            "SELECT COUNT(*) FROM detections"
        ).fetchone()[0]

        print("\nSO BAN GHI TRUOC:", before)

        # ==================================
        # 3. KIEM TRA COT SNAPSHOT_PATH
        # ==================================

        columns = conn.execute(
            "PRAGMA table_info(detections)"
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        # ==================================
        # 4. THEM COT ANH BANG CHUNG
        # ==================================

        if "snapshot_path" not in column_names:

            conn.execute(
                """
                ALTER TABLE detections
                ADD COLUMN snapshot_path TEXT
                """
            )

            conn.commit()

            print(
                "DA THEM COT snapshot_path!"
            )

        else:

            print(
                "Cot snapshot_path da ton tai."
            )

        # ==================================
        # 5. KIEM TRA SAU KHI CAP NHAT
        # ==================================

        after = conn.execute(
            "SELECT COUNT(*) FROM detections"
        ).fetchone()[0]

        columns_after = conn.execute(
            "PRAGMA table_info(detections)"
        ).fetchall()

        print("\n===== KET QUA =====")

        print("DATABASE:", DB_PATH)

        print("So ban ghi truoc:", before)
        print("So ban ghi sau:", after)

        print("\nDANH SACH COT:")

        for column in columns_after:

            print(
                column["name"],
                "-",
                column["type"]
            )

        if before != after:

            raise RuntimeError(
                "So luong ban ghi thay doi!"
            )

        print("\nCAP NHAT DATABASE THANH CONG!")
        print("DU LIEU CU DUOC GIU NGUYEN!")

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()
