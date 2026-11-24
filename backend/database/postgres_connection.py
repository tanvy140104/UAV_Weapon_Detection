"""Transactional PostgreSQL connections shared by backend services."""
import psycopg
from psycopg.rows import dict_row
from backend.config import database_options


class DatabaseNotConfigured(RuntimeError):
    pass


def get_pg_connection(password=None):
    options = database_options(password)
    if not options["password"]:
        raise DatabaseNotConfigured("Chua cau hinh UAV_PG_PASSWORD")
    return psycopg.connect(**options, row_factory=dict_row)
