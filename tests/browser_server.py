"""Test-only HTTP server with deterministic AI; never used by the demo launcher."""
import os

if os.getenv("UAV_TEST_ISOLATED") != "1" or os.getenv("UAV_PG_DATABASE") != "uav_backend_test":
    raise SystemExit("This server requires the isolated backend test runner.")

from backend.main_pg import app
import backend.services.video_service_pg as video_module
import backend.detection_api as detection_module

def fixture_detection(frame):
    return [{"label": "knife", "confidence": 0.9,
             "bbox": {"x1": 40, "y1": 50, "x2": 160, "y2": 180}}]

video_module.detect_frame = fixture_detection
detection_module.detect_frame = fixture_detection

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ["UAV_TEST_HTTP_PORT"]), log_level="warning")
