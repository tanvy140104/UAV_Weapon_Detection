"""Detection events, duplicate suppression, atomic DB/evidence writes and queries."""
import logging
import math
from datetime import datetime, timezone

from backend.database.postgres_connection import get_pg_connection
from backend.services.evidence_service import evidence_service

logger = logging.getLogger(__name__)


def utc_naive(value):
    if value is not None and value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def serialize_record(row):
    item = dict(row)
    if item.get("detected_at") is not None:
        item["detected_at"] = item["detected_at"].strftime("%Y-%m-%d %H:%M:%S")
    return item


class DetectionHistoryService:
    cooldown_seconds = 5
    valid_labels = {"knife", "stick", "gun"}
    valid_statuses = {"NEW", "CONFIRMED", "FALSE_POSITIVE"}

    def validate_detection(self, detection):
        if not isinstance(detection, dict):
            raise ValueError("Detection must be an object")
        try:
            label = detection["label"]
            confidence = float(detection["confidence"])
            bbox = detection["bbox"]
            x1, y1, x2, y2 = (float(bbox[k]) for k in ("x1", "y1", "x2", "y2"))
            if label not in self.valid_labels:
                raise ValueError("Invalid label")
            if not math.isfinite(confidence) or not 0 <= confidence <= 1:
                raise ValueError("Confidence must be in [0, 1]")
            if not all(math.isfinite(v) for v in (x1, y1, x2, y2)):
                raise ValueError("Coordinates must be finite")
            if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
                raise ValueError("Invalid bounding box")
        except (KeyError, TypeError, OverflowError) as error:
            raise ValueError("Invalid detection fields") from error
        return dict(label=label, confidence=confidence, x1=x1, y1=y1, x2=x2, y2=y2)

    def save_detections(self, session_id, detections, frame=None):
        session_id = evidence_service.validate_session_id(session_id)
        if not isinstance(detections, list):
            raise ValueError("Detections must be a list")
        valid = [self.validate_detection(item) for item in detections]
        if not valid:
            return {"saved": 0, "skipped": 0, "detection_ids": []}

        created_images = []
        ids = []
        skipped = 0
        try:
            with get_pg_connection() as conn:
                session = conn.execute(
                    "SELECT status FROM sessions WHERE session_id = %s FOR UPDATE",
                    (session_id,),
                ).fetchone()
                if session is None:
                    raise LookupError("Session not found")
                # This check shares the row lock used by stop_session: no late writes.
                if session["status"] != "RUNNING":
                    return {"saved": 0, "skipped": len(valid), "detection_ids": []}
                for item in valid:
                    recent = conn.execute(
                        """SELECT detection_id FROM detections
                           WHERE session_id = %s AND label = %s
                           AND detected_at >= (
                               (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
                               - (%s * INTERVAL '1 second'))
                           LIMIT 1""",
                        (session_id, item["label"], self.cooldown_seconds),
                    ).fetchone()
                    if recent:
                        skipped += 1
                        continue
                    row = conn.execute(
                        """INSERT INTO detections
                           (session_id, label, confidence, x1, y1, x2, y2)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)
                           RETURNING detection_id""",
                        (session_id, item["label"], item["confidence"],
                         item["x1"], item["y1"], item["x2"], item["y2"]),
                    ).fetchone()
                    detection_id = row["detection_id"]
                    if frame is not None:
                        relative = evidence_service.save_snapshot(frame, session_id, detection_id)
                        created_images.append(relative)
                        conn.execute(
                            "UPDATE detections SET snapshot_path = %s WHERE detection_id = %s",
                            (relative, detection_id),
                        )
                    ids.append(detection_id)
        except Exception:
            # A rolled-back event must not leave an unlinked JPEG.
            for relative in created_images:
                try:
                    evidence_service.get_snapshot_path(relative).unlink(missing_ok=True)
                except (ValueError, OSError):
                    logger.warning("Could not clean rolled-back evidence", exc_info=True)
            raise
        return {"saved": len(ids), "skipped": skipped, "detection_ids": ids}

    def _filters(self, session_id=None, label=None, alert_status=None,
                 date_from=None, date_to=None):
        if label is not None and label not in self.valid_labels:
            raise ValueError("Invalid label")
        if alert_status is not None and alert_status not in self.valid_statuses:
            raise ValueError("Invalid alert status")
        date_from, date_to = utc_naive(date_from), utc_naive(date_to)
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be before date_to")
        clauses, params = [], []
        for column, operator, value in (
            ("session_id", "=", session_id), ("label", "=", label),
            ("alert_status", "=", alert_status),
            ("detected_at", ">=", date_from), ("detected_at", "<=", date_to),
        ):
            if value is not None:
                clauses.append(f"{column} {operator} %s")
                params.append(value)
        return (" WHERE " + " AND ".join(clauses) if clauses else ""), params

    def get_history_page(self, session_id=None, limit=50, offset=0, **filters):
        if not 1 <= limit <= 500 or offset < 0:
            raise ValueError("Invalid pagination")
        where, params = self._filters(session_id=session_id, **filters)
        with get_pg_connection() as conn:
            # One snapshot keeps total/page consistent while monitoring inserts events.
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            total = conn.execute(
                "SELECT COUNT(*) AS total FROM detections" + where, params,
            ).fetchone()["total"]
            rows = conn.execute(
                "SELECT * FROM detections" + where
                + " ORDER BY detection_id DESC LIMIT %s OFFSET %s",
                [*params, limit, offset],
            ).fetchall()
        return {"status": "success", "count": len(rows), "total": total,
                "limit": limit, "offset": offset,
                "detections": [serialize_record(row) for row in rows]}

    def get_history(self, session_id=None, limit=50):
        return self.get_history_page(session_id=session_id, limit=limit)["detections"]


detection_history_service_pg = DetectionHistoryService()
