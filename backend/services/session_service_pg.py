"""Session persistence and transitions, serialized with PostgreSQL row locks."""
from uuid import uuid4
from backend.database.postgres_connection import get_pg_connection
from backend.schemas.session import SessionResponse, SessionStartRequest

SESSION_COLUMNS = "session_id, source_type, source, status, created_at, last_error"


class SessionService:
    def create_session(self, request: SessionStartRequest) -> SessionResponse:
        with get_pg_connection() as conn:
            row = conn.execute(
                f"""INSERT INTO sessions (session_id, source_type, source, status)
                    VALUES (%s, %s, %s, 'STOPPED') RETURNING {SESSION_COLUMNS}""",
                (str(uuid4()), request.source_type, request.source),
            ).fetchone()
        return SessionResponse(**row)

    def get_session(self, session_id):
        row = self.get_session_config(session_id)
        return SessionResponse(**row) if row else None

    def get_session_config(self, session_id):
        with get_pg_connection() as conn:
            return conn.execute(
                f"SELECT {SESSION_COLUMNS} FROM sessions WHERE session_id = %s",
                (session_id,),
            ).fetchone()

    def get_all_sessions(self, limit=50, offset=0):
        with get_pg_connection() as conn:
            rows = conn.execute(
                f"""SELECT {SESSION_COLUMNS} FROM sessions
                    ORDER BY created_at DESC, session_id DESC LIMIT %s OFFSET %s""",
                (limit, offset),
            ).fetchall()
        return [SessionResponse(**row) for row in rows]

    def update_session_status(self, session_id, new_status):
        transitions = {
            "STOPPED": {"RUNNING"},
            "RUNNING": {"STOPPED", "ERROR"},
            "ERROR": {"STOPPED"},
        }
        with get_pg_connection() as conn:
            row = conn.execute(
                "SELECT status FROM sessions WHERE session_id = %s FOR UPDATE",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            if new_status not in transitions.get(row["status"], set()):
                raise ValueError(f"Cannot change status from {row['status']} to {new_status}")
            row = conn.execute(
                f"""UPDATE sessions SET status = %s, last_error = NULL
                    WHERE session_id = %s RETURNING {SESSION_COLUMNS}""",
                (new_status, session_id),
            ).fetchone()
        return SessionResponse(**row)

    def mark_stream_error(self, session_id):
        # Stopping must win over an error that arrives late from the stream.
        with get_pg_connection() as conn:
            conn.execute(
                """UPDATE sessions SET status = 'ERROR', last_error = %s
                   WHERE session_id = %s AND status = 'RUNNING'""",
                ("Monitoring failed. Check video, AI and database; see server log.", session_id),
            )


session_service_pg = SessionService()
