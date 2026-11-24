"""Start the local backend using .env or a hidden password prompt."""
import getpass
import logging
import os

from backend.config import PROJECT_ROOT
from backend.database.postgres_connection import get_pg_connection
import uvicorn


def main():
    if not os.getenv("UAV_PG_PASSWORD"):
        os.environ["UAV_PG_PASSWORD"] = getpass.getpass("Mat khau PostgreSQL uav_backend: ")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # Fail early with an actionable message rather than opening a broken demo.
    try:
        with get_pg_connection() as conn:
            conn.execute("SELECT session_id, last_error FROM sessions LIMIT 0")
            conn.execute("SELECT detection_id, snapshot_path FROM detections LIMIT 0")
    except Exception:
        raise SystemExit(
            "PostgreSQL chua san sang. Kiem tra .env, dich vu PostgreSQL va chay "
            "python -m backend.database.init_pg"
        )
    if not (PROJECT_ROOT / "models/trained/gks_field_ft_10e/weights/best.pt").is_file():
        raise SystemExit("Khong tim thay model AI. Kiem tra thu muc models/trained.")
    host, port = os.getenv("UAV_HOST", "127.0.0.1"), int(os.getenv("UAV_PORT", "8003"))
    print(f"Web: http://{host}:{port}/web/")
    print(f"API: http://{host}:{port}/docs")
    uvicorn.run("backend.main_pg:app", host=host, port=port, reload=False, workers=1)


if __name__ == "__main__":
    main()
