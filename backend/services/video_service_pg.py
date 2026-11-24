"""Video transport, monitor ownership and orchestration of detection persistence."""
import logging
import os
import threading
import time
from uuid import uuid4
from pathlib import Path

import cv2

from backend.config import PROJECT_ROOT
from backend.database.postgres_connection import get_pg_connection
from backend.services.session_service_pg import session_service_pg as session_service
from backend.services.detection_service import detect_frame
from backend.services.detection_history_service_pg import detection_history_service_pg as history_service

logger = logging.getLogger(__name__)


class MonitorBusy(ValueError):
    pass


class VideoService:
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.video_path = PROJECT_ROOT / "data" / "videos" / "test.mp4"
        self.history_interval = 1.0
        self.ai_colors = {"knife": (0, 0, 255), "stick": (0, 165, 255), "gun": (255, 0, 255)}
        self._lock = threading.Lock()
        self._monitors = {}  # session_id -> (ownership token, capture source)

    def get_video_path(self, session_id=None):
        if session_id is None:
            path = self.video_path.resolve()
        else:
            session = session_service.get_session_config(session_id)
            if session is None:
                raise LookupError("Session not found")
            if session["source_type"] != "file":
                raise ValueError("Only file source is supported")
            source = Path(session["source"])
            path = (self.project_root / source).resolve()
            if source.is_absolute() or not path.is_relative_to(
                (self.project_root / "data" / "videos").resolve()
            ):
                raise ValueError("Video path is outside data/videos")
        if not path.is_file():
            raise FileNotFoundError("Video file not found")
        return path

    def get_capture_source(self, session_id=None):
        if session_id is None:
            return str(self.get_video_path())
        session = session_service.get_session_config(session_id)
        if session is None:
            raise LookupError("Session not found")
        if session["source_type"] == "file":
            return str(self.get_video_path(session_id))
        if session["source_type"] == "camera":
            value = str(session["source"]).strip()
            if not value.isascii() or not value.isdigit() or int(value) > 99:
                raise ValueError("Invalid camera index")
            return int(value)
        raise ValueError("Unsupported video source type")

    def assert_monitor_available(self, session_id, source=None):
        with self._lock:
            if session_id in self._monitors or (
                isinstance(source, int)
                and any(item[1] == source for item in self._monitors.values())
            ):
                raise MonitorBusy("Monitor is already open. Close the existing stream first.")

    def reserve_monitor(self, session_id):
        source = self.get_capture_source(session_id)
        token = uuid4().hex
        with self._lock:
            if session_id in self._monitors or (
                isinstance(source, int)
                and any(item[1] == source for item in self._monitors.values())
            ):
                raise MonitorBusy("Monitor is already open. Close the existing stream first.")
            self._monitors[session_id] = (token, source)
        return token

    def release_monitor(self, session_id, token, finish=False):
        with self._lock:
            current = self._monitors.get(session_id)
            if current is None or current[0] != token:
                return
            try:
                if finish:
                    with get_pg_connection() as conn:
                        conn.execute(
                            """UPDATE sessions SET status = 'STOPPED'
                               WHERE session_id = %s AND status = 'RUNNING'""",
                            (session_id,),
                        )
            except Exception:
                logger.exception("Could not finalize session %s", session_id)
            finally:
                del self._monitors[session_id]

    def open_capture(self, source):
        if isinstance(source, int):
            return cv2.VideoCapture(source, cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY)
        return cv2.VideoCapture(source)

    def get_video_info(self, session_id=None):
        source = self.get_capture_source(session_id)
        cap = self.open_capture(source)
        try:
            if not cap.isOpened():
                raise RuntimeError("Cannot open video source")
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("Cannot read video frame")
            height, width = frame.shape[:2]
            fps = cap.get(cv2.CAP_PROP_FPS)
            camera = isinstance(source, int)
            total = 0 if camera else int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            return {
                "video_name": f"camera_{source}" if camera else Path(source).name,
                "status": "READY", "width": width, "height": height, "fps": fps,
                "total_frames": total,
                "duration": round(total / fps, 2) if fps > 0 else 0.0,
            }
        finally:
            cap.release()

    def get_first_frame_jpeg(self, session_id=None):
        cap = self.open_capture(self.get_capture_source(session_id))
        try:
            if not cap.isOpened():
                raise RuntimeError("Cannot open video")
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError("Cannot read video frame")
            encoded, buffer = cv2.imencode(".jpg", frame)
            if not encoded:
                raise RuntimeError("Cannot encode JPEG")
            return buffer.tobytes()
        finally:
            cap.release()

    def draw_ai_detections(self, frame, detections):
        height, width = frame.shape[:2]
        for detection in detections:
            box = detection["bbox"]
            x1, x2 = [max(0, min(int(box[k]), width - 1)) for k in ("x1", "x2")]
            y1, y2 = [max(0, min(int(box[k]), height - 1)) for k in ("y1", "y2")]
            if x2 <= x1 or y2 <= y1:
                continue
            color = self.ai_colors.get(detection["label"], (0, 255, 0))
            text = f"{detection['label'].upper()} {detection['confidence']:.1%}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, text, (x1, max(20, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)
        return frame

    def generate_video_stream(self, session_id=None, ai_enabled=False):
        source = self.get_capture_source(session_id)
        cap = self.open_capture(source)
        last_save = float("-inf")
        try:
            if not cap.isOpened():
                raise RuntimeError("Cannot open video stream")
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_delay = 1.0 / fps if 0 < fps <= 120 else 1.0 / 15
            while True:
                started = time.monotonic()
                if ai_enabled:
                    session = session_service.get_session_config(session_id)
                    if session is None or session["status"] != "RUNNING":
                        break
                ok, frame = cap.read()
                if not ok:
                    if isinstance(source, int):
                        raise RuntimeError("Camera disconnected")
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = cap.read()
                    if not ok:
                        raise RuntimeError("Cannot decode video")
                if ai_enabled:
                    detections = detect_frame(frame)
                    frame = self.draw_ai_detections(frame, detections)
                    now = time.monotonic()
                    if detections and now - last_save >= self.history_interval:
                        history_service.save_detections(session_id, detections, frame=frame)
                        last_save = now
                    cv2.putText(frame, "AI ON - YOLO11n", (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
                encoded, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if not encoded:
                    raise RuntimeError("Cannot encode video frame")
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
                if not isinstance(source, int):
                    time.sleep(max(0, frame_delay - (time.monotonic() - started)))
        finally:
            cap.release()

    def generate_monitoring_stream(self, session_id, token=None):
        token = token or self.reserve_monitor(session_id)
        generator = self.generate_video_stream(session_id, ai_enabled=True)
        try:
            yield from generator
        except Exception:
            logger.exception("Monitoring failed for session %s", session_id)
            try:
                session_service.mark_stream_error(session_id)
            except Exception:
                logger.exception("Could not record monitoring error for %s", session_id)
        finally:
            generator.close()
            self.release_monitor(session_id, token, finish=True)


video_service = VideoService()
