
# ==========================================
# TAO VIDEO SERVICE POSTGRESQL
# KHONG CHINH SUA FILE VIDEO SERVICE GOC
# ==========================================

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    PROJECT_ROOT
    / "backend"
    / "services"
    / "video_service.py"
)

TARGET = (
    PROJECT_ROOT
    / "backend"
    / "services"
    / "video_service_pg.py"
)


def main():

    print("===== PREPARE VIDEO SERVICE PG =====")

    if not SOURCE.is_file():
        raise FileNotFoundError(
            f"Khong tim thay file goc: {SOURCE}"
        )

    # Tranh ghi de len file da chinh sua
    if TARGET.exists():
        raise FileExistsError(
            f"File da ton tai: {TARGET}"
        )

    # Doc code goc
    code = SOURCE.read_text(
        encoding="utf-8"
    )

    # ======================================
    # 1. THAY IMPORT SESSION SERVICE
    # ======================================

    replacements = [
        (
            "from backend.services.session_service "
            "import session_service",

            "from backend.services.session_service_pg "
            "import session_service_pg as session_service"
        ),

        # ==================================
        # 2. THAY DETECTION HISTORY SERVICE
        # ==================================
        (
            "from backend.services.detection_history_service import (\n"
            "    detection_history_service\n"
            ")",

            "from backend.services.detection_history_service_pg import (\n"
            "    detection_history_service_pg as detection_history_service\n"
            ")"
        ),

        # ==================================
        # 3. THAY KET NOI DATABASE
        # ==================================
        (
            "from backend.database.connection "
            "import get_connection",

            "from backend.database.postgres_connection "
            "import get_pg_connection as get_connection"
        ),

        # ==================================
        # 4. THAY CU PHAP UPDATE SNAPSHOT
        # ==================================
        (
            "SET snapshot_path = ?",
            "SET snapshot_path = %s"
        ),
        (
            "WHERE detection_id = ?",
            "WHERE detection_id = %s"
        ),
        (
            "AND session_id = ?",
            "AND session_id = %s"
        )
    ]

    # Moi doan can thay phai ton tai
    # dung 1 lan trong file goc
    for old, new in replacements:

        count = code.count(old)

        if count != 1:
            raise RuntimeError(
                f"Khong the thay an toan: {old!r}. "
                f"So lan tim thay: {count}"
            )

        code = code.replace(old, new, 1)

    # ======================================
    # 5. CAP NHAT CHU THICH
    # ======================================

    code = code.replace(
        "Ket noi SQLite",
        "Ket noi PostgreSQL"
    )

    code = code.replace(
        "CAP NHAT DUONG DAN SQLITE",
        "CAP NHAT DUONG DAN POSTGRESQL"
    )

    code = code.replace(
        "Luu lich su vao SQLite",
        "Luu lich su vao PostgreSQL"
    )

    # Kiem tra cu phap Python truoc khi luu
    compile(
        code,
        str(TARGET),
        "exec"
    )

    # ======================================
    # 6. TAO FILE MOI
    # ======================================

    TARGET.write_text(
        code,
        encoding="utf-8"
    )

    print("File goc:", SOURCE)
    print("File moi:", TARGET)

    print("\nDA THAY:")
    print("1. SessionService -> PostgreSQL")
    print("2. DetectionHistoryService -> PostgreSQL")
    print("3. Database connection -> PostgreSQL")
    print("4. SQL placeholders -> %s")

    print("\nKIEM TRA CU PHAP: PASS")
    print("VIDEO SERVICE PG: CREATED")
    print("FILE GOC: KHONG THAY DOI")


if __name__ == "__main__":
    main()
