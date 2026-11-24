"""Environment variables override the local .env file."""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)


def database_options(password=None):
    return {
        "host": os.getenv("UAV_PG_HOST", "127.0.0.1"),
        "port": int(os.getenv("UAV_PG_PORT", "5432")),
        "dbname": os.getenv("UAV_PG_DATABASE", "uav_weapon_detection"),
        "user": os.getenv("UAV_PG_USER", "uav_backend"),
        "password": password if password is not None else os.getenv("UAV_PG_PASSWORD"),
        "connect_timeout": 5,
        "options": "-c timezone=UTC -c statement_timeout=10000 -c lock_timeout=5000",
        "application_name": "uav_backend",
    }
