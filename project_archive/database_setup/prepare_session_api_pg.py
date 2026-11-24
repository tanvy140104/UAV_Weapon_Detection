
# ==========================================
# PREPARE SESSION API - POSTGRESQL
# UAV WEAPON DETECTION
# ==========================================

from pathlib import Path


# 1. Xac dinh thu muc du an
PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    PROJECT_ROOT
    / "backend"
    / "api"
    / "session.py"
)

TARGET = (
    PROJECT_ROOT
    / "backend"
    / "api"
    / "session_pg.py"
)


def main():

    print("===== PREPARE SESSION API PG =====")

    # 2. Kiem tra file goc
    if not SOURCE.is_file():
        raise FileNotFoundError(
            f"Khong tim thay: {SOURCE}"
        )

    # Khong ghi de file da ton tai
    if TARGET.exists():
        raise FileExistsError(
            f"File da ton tai: {TARGET}"
        )

    # 3. Doc code API goc
    code = SOURCE.read_text(
        encoding="utf-8"
    )

    # 4. Chuyen cac Service sang PostgreSQL
    replacements = [
        (
            "from backend.services.video_service "
            "import video_service",

            "from backend.services.video_service_pg "
            "import video_service"
        ),
        (
            "from backend.services.session_service "
            "import session_service",

            "from backend.services.session_service_pg "
            "import session_service_pg as session_service"
        )
    ]

    for old, new in replacements:

        count = code.count(old)

        if count != 1:
            raise RuntimeError(
                f"Khong the thay an toan: {old}. "
                f"Tim thay {count} lan."
            )

        code = code.replace(old, new, 1)

    # 5. Cap nhat chu thich
    code = code.replace(
        "SQLite",
        "PostgreSQL"
    )

    # 6. Kiem tra cu phap truoc khi luu
    compile(
        code,
        str(TARGET),
        "exec"
    )

    # 7. Tao file moi
    TARGET.write_text(
        code,
        encoding="utf-8"
    )

    print("\nFILE MOI:", TARGET)
    print("SessionService: PostgreSQL")
    print("VideoService: PostgreSQL")
    print("API endpoints: GIU NGUYEN")

    print("\nKIEM TRA CU PHAP: PASS")
    print("SESSION API PG: CREATED")
    print("FILE GOC: KHONG THAY DOI")


if __name__ == "__main__":
    main()
