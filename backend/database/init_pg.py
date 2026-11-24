"""Run with python -m backend.database.init_pg after creating the database/user."""
import getpass
import os
from pathlib import Path
from backend.database.postgres_connection import get_pg_connection


def init_database():
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with get_pg_connection() as connection:
        connection.execute(schema)


if __name__ == "__main__":
    if not os.getenv("UAV_PG_PASSWORD"):
        os.environ["UAV_PG_PASSWORD"] = getpass.getpass("Mat khau PostgreSQL: ")
    init_database()
    print("PostgreSQL schema ready. Existing history preserved.")
