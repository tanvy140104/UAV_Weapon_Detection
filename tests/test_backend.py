"""Real PostgreSQL tests; only AI/camera hardware and injected faults are substituted."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import cv2
import numpy as np
import psycopg
from fastapi.testclient import TestClient

from backend.main_pg import app
from backend.database.init_pg import init_database
from backend.database.postgres_connection import get_pg_connection
from backend.schemas.session import SessionStartRequest
from backend.services.session_service_pg import session_service_pg as sessions
from backend.services.detection_history_service_pg import detection_history_service_pg as history
from backend.services.evidence_service import evidence_service
from backend.services.video_service_pg import video_service, MonitorBusy

DETECTION = {"label": "knife", "confidence": 0.9,
             "bbox": {"x1": 10, "y1": 10, "x2": 40, "y2": 50}}


class FakeCapture:
    def __init__(self):
        self.released = False
    def isOpened(self):
        return True
    def read(self):
        return True, np.zeros((80, 100, 3), dtype=np.uint8)
    def get(self, prop):
        return 15.0
    def set(self, prop, value):
        return True
    def release(self):
        self.released = True


class BackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (os.getenv("UAV_TEST_ISOLATED") != "1"
                or os.getenv("UAV_PG_DATABASE") != "uav_backend_test"):
            raise unittest.SkipTest("Use python run_backend_tests.py for an isolated database")
        root = Path(os.environ["UAV_TEST_RUN_DIR"])
        cls.evidence_root = root / "artifacts"
        cls.evidence_root.mkdir()
        cls.root_patch = patch.object(evidence_service, "project_root", cls.evidence_root)
        cls.dir_patch = patch.object(evidence_service, "evidence_dir", cls.evidence_root / "data/evidence")
        cls.root_patch.start()
        cls.dir_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.dir_patch.stop()
        cls.root_patch.stop()

    def setUp(self):
        with get_pg_connection() as conn:
            conn.execute("TRUNCATE detections, sessions RESTART IDENTITY")
        video_service._monitors.clear()
        self.client = TestClient(app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def create(self, running=False):
        response = self.client.post("/sessions", json={
            "source_type": "file", "source": "data/videos/test.mp4",
        })
        self.assertEqual(response.status_code, 201, response.text)
        session_id = response.json()["session_id"]
        if running:
            started = self.client.post(f"/sessions/{session_id}/start")
            self.assertEqual(started.status_code, 200, started.text)
        return session_id

    def save(self, session_id, label="knife", frame=None):
        return history.save_detections(session_id, [{**DETECTION, "label": label}], frame=frame)

    def test_health_web_and_openapi(self):
        for path in ("/health", "/health/ready", "/web/", "/openapi.json"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, response.text[:200])
            self.assertIn("x-request-id", response.headers)
        self.assertIn("/api/history", self.client.get("/openapi.json").json()["paths"])

    def test_database_failure_is_503_without_driver_details(self):
        with patch("backend.services.session_service_pg.get_pg_connection",
                   side_effect=psycopg.OperationalError("secret-driver-info")):
            response = self.client.get("/sessions")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret-driver-info", response.text)
        self.assertIn("request_id", response.json())

    def test_readiness_detects_database_failure(self):
        with patch("backend.api.health.get_pg_connection",
                   side_effect=psycopg.OperationalError("offline")):
            response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["database"], "unavailable")

    def test_source_validation_before_database_write(self):
        for data in (
            {"source_type": "rtsp", "source": "rtsp://host"},
            {"source_type": "camera", "source": "-1"},
            {"source_type": "camera", "source": "100"},
            {"source_type": "camera", "source": "abc"},
            {"source_type": "file", "source": "data/videos/../../DEMO_BACKEND.md"},
            {"source_type": "file", "source": str(Path("data/videos/test.mp4").resolve())},
            {"source_type": "file", "source": "   "},
            {"source_type": "file", "source": "data/videos/test.mp4", "unknown": True},
        ):
            with self.subTest(data=data):
                self.assertEqual(self.client.post("/sessions", json=data).status_code, 422)
        self.assertEqual(self.client.get("/sessions").json(), [])

    def test_camera_source_normalized(self):
        result = self.client.post("/sessions", json={"source_type": "camera", "source": " 01 "})
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.json()["source"], "1")

    def test_session_lifecycle_and_conflicts(self):
        session_id = self.create()
        self.assertEqual(self.client.post(f"/sessions/{session_id}/stop").status_code, 409)
        self.assertEqual(self.client.post(f"/sessions/{session_id}/start").status_code, 200)
        self.assertEqual(self.client.post(f"/sessions/{session_id}/start").status_code, 409)
        self.assertEqual(self.client.post(f"/sessions/{session_id}/stop").json()["status"], "STOPPED")
        self.assertEqual(self.client.get("/sessions/missing").status_code, 404)
        self.assertEqual(self.client.post("/sessions/missing/start").status_code, 404)
        self.assertEqual(self.client.post("/sessions/missing/stop").status_code, 404)
        response = self.client.get(f"/sessions/{session_id}").json()
        self.assertEqual(response["source"], "data/videos/test.mp4")
        self.assertIsNotNone(response["created_at"])

    def test_missing_video_does_not_start_session(self):
        response = self.client.post("/sessions", json={"source": "data/videos/absent.mp4"})
        session_id = response.json()["session_id"]
        self.assertEqual(self.client.post(f"/sessions/{session_id}/start").status_code, 404)
        self.assertEqual(sessions.get_session(session_id).status, "STOPPED")

    def test_session_list_pagination(self):
        for _ in range(3):
            self.create()
        self.assertEqual(len(self.client.get("/sessions?limit=2&offset=1").json()), 2)
        self.assertEqual(self.client.get("/sessions?limit=0").status_code, 422)
        self.assertEqual(self.client.get("/sessions?offset=-1").status_code, 422)

    def test_atomic_history_evidence_alert_workflow(self):
        session_id = self.create(running=True)
        frame = np.zeros((80, 100, 3), dtype=np.uint8)
        result = self.save(session_id, frame=frame)
        detection_id = result["detection_ids"][0]
        self.assertEqual(result["saved"], 1)
        self.assertEqual(self.save(session_id)["skipped"], 1)
        self.save(session_id, label="stick")
        page = self.client.get(f"/api/history?session_id={session_id}").json()
        self.assertEqual(page["total"], 2)
        row = next(item for item in page["detections"] if item["label"] == "knife")
        self.assertTrue(row["snapshot_path"])
        image = self.client.get(f"/api/evidence/{detection_id}/image")
        self.assertEqual(image.status_code, 200)
        self.assertIsNotNone(cv2.imdecode(np.frombuffer(image.content, np.uint8), cv2.IMREAD_COLOR))
        for status in ("CONFIRMED", "FALSE_POSITIVE", "NEW"):
            updated = self.client.patch(f"/api/alerts/{detection_id}/status",
                                        json={"alert_status": status})
            self.assertEqual(updated.status_code, 200)
            self.assertEqual(updated.json()["detection"]["alert_status"], status)
        self.client.post(f"/sessions/{session_id}/stop")
        self.assertEqual(self.save(session_id, label="gun")["saved"], 0)

    def test_concurrent_detection_writes_are_deduplicated(self):
        session_id = self.create(running=True)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.save(session_id), range(4)))
        self.assertEqual(sum(row["saved"] for row in results), 1)
        self.assertEqual(history.get_history_page()["total"], 1)

    def test_concurrent_start_has_one_winner(self):
        session_id = self.create()
        def start(_):
            try:
                return sessions.update_session_status(session_id, "RUNNING").status
            except ValueError:
                return "CONFLICT"
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(start, range(2))), ["RUNNING", "CONFLICT"])

    def test_invalid_detections_never_write(self):
        session_id = self.create(running=True)
        for item in (
            {}, {**DETECTION, "label": "other"},
            {**DETECTION, "confidence": float("nan")},
            {**DETECTION, "bbox": {"x1": 40, "y1": 10, "x2": 20, "y2": 30}},
        ):
            with self.subTest(item=item), self.assertRaises(ValueError):
                history.save_detections(session_id, [item])
        self.assertEqual(history.get_history_page()["total"], 0)

    def test_evidence_failure_rolls_back_whole_batch(self):
        session_id = self.create(running=True)
        frame = np.zeros((80, 100, 3), dtype=np.uint8)
        original = evidence_service.save_snapshot
        paths = []
        def save_then_fail(frame, sid, detection_id):
            if paths:
                raise OSError("Injected disk failure")
            path = original(frame, sid, detection_id)
            paths.append(path)
            return path
        with patch.object(evidence_service, "save_snapshot", side_effect=save_then_fail):
            with self.assertRaises(OSError):
                history.save_detections(session_id, [DETECTION, {**DETECTION, "label": "gun"}],
                                        frame=frame)
        self.assertEqual(history.get_history_page()["total"], 0)
        self.assertFalse((self.evidence_root / paths[0]).exists())

    def test_history_filters_pagination_and_parameterized_queries(self):
        first = self.create(running=True)
        second = self.create(running=True)
        self.save(first)
        self.save(first, label="stick")
        self.save(second, label="gun")
        page = self.client.get("/api/history?limit=1&offset=1").json()
        self.assertEqual((page["count"], page["total"], page["offset"]), (1, 3, 1))
        self.assertEqual(self.client.get(f"/api/history?session_id={first}&label=knife").json()["total"], 1)
        self.assertEqual(self.client.get("/api/history?session_id=' OR 1=1 --").json()["total"], 0)
        self.assertEqual(self.client.get("/api/history?date_from=2999-01-01T00:00:00Z").json()["total"], 0)
        self.assertEqual(self.client.get("/api/history?date_from=2026-01-02&date_to=2026-01-01").status_code, 422)
        for query in ("limit=501", "offset=-1", "label=unknown", "alert_status=BAD"):
            self.assertEqual(self.client.get("/api/history?" + query).status_code, 422)

    def test_evidence_missing_and_path_traversal(self):
        self.assertEqual(self.client.get("/api/evidence/9999/image").status_code, 404)
        self.assertEqual(self.client.get("/api/evidence/0/image").status_code, 422)
        session_id = self.create(running=True)
        detection_id = self.save(session_id)["detection_ids"][0]
        self.assertEqual(self.client.get(f"/api/evidence/{detection_id}/image").status_code, 404)
        with get_pg_connection() as conn:
            conn.execute("UPDATE detections SET snapshot_path = %s WHERE detection_id = %s",
                         ("../../DEMO_BACKEND.md", detection_id))
        self.assertEqual(self.client.get(f"/api/evidence/{detection_id}/image").status_code, 400)

    def test_alert_invalid_and_not_found(self):
        self.assertEqual(self.client.patch("/api/alerts/999/status",
                                          json={"alert_status": "CONFIRMED"}).status_code, 404)
        self.assertEqual(self.client.patch("/api/alerts/1/status",
                                          json={"alert_status": "INVALID"}).status_code, 422)

    def test_schema_setup_is_repeatable_and_preserves_data(self):
        self.create()
        init_database()
        init_database()
        self.assertEqual(len(self.client.get("/sessions").json()), 1)

    def test_monitor_requires_running_session(self):
        session_id = self.create()
        self.assertEqual(self.client.get(f"/videos/sessions/{session_id}/monitor").status_code, 409)
        self.assertEqual(self.client.get("/videos/sessions/missing/monitor").status_code, 404)

    def test_monitor_saves_frame_and_disconnect_stops_session(self):
        session_id = self.create(running=True)
        cap = FakeCapture()
        with patch.object(video_service, "open_capture", return_value=cap), patch(
            "backend.services.video_service_pg.detect_frame", return_value=[DETECTION]
        ):
            stream = video_service.generate_monitoring_stream(session_id)
            self.assertTrue(next(stream).startswith(b"--frame"))
            stream.close()
        self.assertTrue(cap.released)
        self.assertEqual(sessions.get_session(session_id).status, "STOPPED")
        row = history.get_history(session_id)[0]
        self.assertTrue(evidence_service.get_snapshot_path(row["snapshot_path"]).is_file())

    def test_monitor_error_visible_and_recoverable(self):
        session_id = self.create(running=True)
        cap = FakeCapture()
        with patch.object(video_service, "open_capture", return_value=cap), patch(
            "backend.services.video_service_pg.detect_frame", side_effect=RuntimeError("AI failed")
        ):
            self.assertEqual(list(video_service.generate_monitoring_stream(session_id)), [])
        self.assertTrue(cap.released)
        response = self.client.get(f"/sessions/{session_id}").json()
        self.assertEqual(response["status"], "ERROR")
        self.assertTrue(response["last_error"])
        self.assertEqual(self.client.post(f"/sessions/{session_id}/stop").json()["status"], "STOPPED")
        self.assertEqual(self.client.post(f"/sessions/{session_id}/start").status_code, 200)

    def test_monitor_reservation_conflict_and_old_token(self):
        session_id = self.create(running=True)
        token = video_service.reserve_monitor(session_id)
        self.assertEqual(self.client.get(f"/videos/sessions/{session_id}/monitor").status_code, 409)
        self.client.post(f"/sessions/{session_id}/stop")
        self.assertEqual(self.client.post(f"/sessions/{session_id}/start").status_code, 409)
        video_service.release_monitor(session_id, "wrong-token", finish=True)
        self.assertIn(session_id, video_service._monitors)
        video_service.release_monitor(session_id, token, finish=True)
        self.assertEqual(self.client.post(f"/sessions/{session_id}/start").status_code, 200)

    def test_video_sample_and_image_validation(self):
        self.assertEqual(self.client.get("/videos/info").status_code, 200)
        self.assertEqual(self.client.get("/videos/frame").headers["content-type"], "image/jpeg")
        for typ, content, code in (
            ("text/plain", b"abc", 415), ("image/jpeg", b"", 400),
            ("image/jpeg", b"bad", 400),
        ):
            response = self.client.post("/api/detection/image", content=content,
                                        headers={"content-type": typ})
            self.assertEqual(response.status_code, code)

    def test_database_write_failure_cleans_evidence(self):
        session_id = self.create(running=True)
        with get_pg_connection() as conn:
            conn.execute("""CREATE FUNCTION reject_test_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'Injected DB failure'; END $$""")
            conn.execute("""CREATE TRIGGER reject_test_snapshot BEFORE UPDATE ON detections
                FOR EACH ROW EXECUTE FUNCTION reject_test_snapshot()""")
        try:
            with self.assertRaises(psycopg.Error):
                self.save(session_id, frame=np.zeros((80, 100, 3), dtype=np.uint8))
            self.assertEqual(history.get_history_page()["total"], 0)
            self.assertEqual(list((evidence_service.evidence_dir / session_id).glob("*.jpg")), [])
        finally:
            with get_pg_connection() as conn:
                conn.execute("DROP TRIGGER reject_test_snapshot ON detections")
                conn.execute("DROP FUNCTION reject_test_snapshot()")

    def test_camera_is_owned_by_one_session(self):
        first = sessions.create_session(SessionStartRequest(source_type="camera", source="0")).session_id
        second = sessions.create_session(SessionStartRequest(source_type="camera", source="0")).session_id
        token = video_service.reserve_monitor(first)
        with self.assertRaises(MonitorBusy):
            video_service.reserve_monitor(second)
        video_service.release_monitor(first, token)
        token = video_service.reserve_monitor(second)
        video_service.release_monitor(second, token)

    def test_image_api_success_failure_and_size_limit(self):
        _, image = cv2.imencode(".jpg", np.zeros((80, 100, 3), dtype=np.uint8))
        with patch("backend.detection_api.detect_frame", return_value=[DETECTION]):
            response = self.client.post("/api/detection/image", content=image.tobytes(),
                                        headers={"content-type": "image/jpeg"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["detection_count"], 1)
        with patch("backend.detection_api.detect_frame", side_effect=RuntimeError("inference offline")):
            response = self.client.post("/api/detection/image", content=image.tobytes(),
                                        headers={"content-type": "image/jpeg"})
        self.assertEqual(response.status_code, 503)
        with patch("backend.detection_api.MAX_IMAGE_BYTES", 20):
            self.assertEqual(self.client.post("/api/detection/image", content=b"x" * 21,
                headers={"content-type": "image/jpeg"}).status_code, 413)

    def test_monitor_preflight_failure_releases_reservation(self):
        session_id = self.create(running=True)
        with patch.object(video_service, "get_video_info", side_effect=RuntimeError("Camera failed")):
            response = self.client.get(f"/videos/sessions/{session_id}/monitor")
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(session_id, video_service._monitors)
        self.assertEqual(sessions.get_session(session_id).status, "ERROR")


if __name__ == "__main__":
    unittest.main()
