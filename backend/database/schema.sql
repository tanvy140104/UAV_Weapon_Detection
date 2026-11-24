-- Additive setup: never removes existing tables or monitoring history.
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK (source_type IN ('file', 'camera', 'rtsp')),
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'STOPPED'
        CHECK (status IN ('STOPPED', 'RUNNING', 'ERROR')),
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    last_error TEXT
);
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS last_error TEXT;

CREATE TABLE IF NOT EXISTS detections (
    detection_id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    label TEXT NOT NULL CHECK (label IN ('knife', 'stick', 'gun')),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    x1 DOUBLE PRECISION NOT NULL CHECK (x1 >= 0),
    y1 DOUBLE PRECISION NOT NULL CHECK (y1 >= 0),
    x2 DOUBLE PRECISION NOT NULL CHECK (x2 > x1),
    y2 DOUBLE PRECISION NOT NULL CHECK (y2 > y1),
    detected_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    alert_status TEXT NOT NULL DEFAULT 'NEW'
        CHECK (alert_status IN ('NEW', 'CONFIRMED', 'FALSE_POSITIVE')),
    snapshot_path TEXT
);
ALTER TABLE detections ADD COLUMN IF NOT EXISTS snapshot_path TEXT;
CREATE INDEX IF NOT EXISTS idx_detections_session_label_time
    ON detections(session_id, label, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_detections_alert_id
    ON detections(alert_status, detection_id DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);
