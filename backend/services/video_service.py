
# ==========================================
# VIDEO SERVICE - VIDEO + YOLO + DATABASE
# VA LUU ANH BANG CHUNG
# ==========================================

import cv2
import time
from pathlib import Path

# Quan ly phien giam sat
from backend.services.session_service import session_service

# AI nhan dien vu khi
from backend.services.detection_service import detect_frame

# Luu lich su phat hien
from backend.services.detection_history_service import (
    detection_history_service
)

# Luu anh JPEG bang chung
from backend.services.evidence_service import evidence_service

# Ket noi SQLite
from backend.database.connection import get_connection


class VideoService:

    def __init__(self):

        # Thu muc goc du an
        self.project_root = Path(__file__).resolve().parents[2]

        # Video mac dinh
        self.video_path = (
            self.project_root / "data" / "videos" / "test.mp4"
        )

        # Mau BGR cua bounding box
        self.ai_colors = {
            "knife": (0, 0, 255),
            "stick": (0, 165, 255),
            "gun": (255, 0, 255)
        }

        # Moi 1 giay moi kiem tra luu lich su
        self.history_interval = 1.0

    # ======================================
    # 1. LAY DUONG DAN VIDEO FILE
    # ======================================

    def get_video_path(
        self,
        session_id: str | None = None
    ) -> Path:

        if session_id is None:
            video_path = self.video_path.resolve()

        else:
            session = session_service.get_session_config(
                session_id
            )

            if session is None:
                raise LookupError("Session not found")

            if session["source_type"] != "file":
                raise ValueError(
                    "Only file source is supported"
                )

            source = Path(session["source"])

            if source.is_absolute():
                raise ValueError(
                    "Absolute paths are not supported"
                )

            video_path = (
                self.project_root / source
            ).resolve()

            allowed_folder = (
                self.project_root / "data" / "videos"
            ).resolve()

            if not video_path.is_relative_to(allowed_folder):
                raise ValueError(
                    "Video path is outside data/videos"
                )

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Video file not found: {video_path}"
            )

        return video_path

    # ======================================
    # 2. XAC DINH NGUON VIDEO
    # ======================================

    def get_capture_source(
        self,
        session_id: str | None = None
    ):

        if session_id is None:
            return str(self.get_video_path())

        session = session_service.get_session_config(
            session_id
        )

        if session is None:
            raise LookupError("Session not found")

        source_type = session["source_type"]
        source = session["source"]

        if source_type == "file":
            return str(self.get_video_path(session_id))

        if source_type == "camera":

            camera_index = str(source).strip()

            if not camera_index.isdigit():
                raise ValueError("Invalid camera index")

            return int(camera_index)

        raise ValueError("Unsupported video source type")

    # ======================================
    # 3. MO FILE MP4 HOAC WEBCAM
    # ======================================

    def open_capture(self, source):

        if isinstance(source, int):
            return cv2.VideoCapture(
                source,
                cv2.CAP_DSHOW
            )

        return cv2.VideoCapture(source)

    # ======================================
    # 4. LAY THONG TIN VIDEO
    # ======================================

    def get_video_info(
        self,
        session_id: str | None = None
    ):

        source = self.get_capture_source(session_id)

        is_camera = isinstance(source, int)

        cap = self.open_capture(source)

        try:

            if not cap.isOpened():
                raise RuntimeError(
                    "Cannot open video source"
                )

            success, frame = cap.read()

            if not success:
                raise RuntimeError(
                    "Cannot read video frame"
                )

            height, width = frame.shape[:2]

            fps = cap.get(cv2.CAP_PROP_FPS)

            if is_camera:

                video_name = f"camera_{source}"
                total_frames = 0
                duration = 0.0

            else:

                video_name = Path(source).name

                total_frames = int(
                    cap.get(cv2.CAP_PROP_FRAME_COUNT)
                )

                duration = (
                    total_frames / fps
                    if fps > 0
                    else 0.0
                )

            return {
                "video_name": video_name,
                "status": "READY",
                "width": width,
                "height": height,
                "fps": fps,
                "total_frames": total_frames,
                "duration": round(duration, 2)
            }

        finally:
            cap.release()

    # ======================================
    # 5. LAY FRAME DAU TIEN DANG JPEG
    # ======================================

    def get_first_frame_jpeg(
        self,
        session_id: str | None = None
    ) -> bytes:

        video_path = self.get_video_path(session_id)

        cap = cv2.VideoCapture(str(video_path))

        try:

            if not cap.isOpened():
                raise RuntimeError(
                    "Cannot open video"
                )

            success, frame = cap.read()

            if not success:
                raise RuntimeError(
                    "Cannot read video frame"
                )

            encoded, buffer = cv2.imencode(
                ".jpg",
                frame
            )

            if not encoded:
                raise RuntimeError(
                    "Cannot encode JPEG"
                )

            return buffer.tobytes()

        finally:
            cap.release()

    # ======================================
    # 6. VE BOUNDING BOX CUA YOLO
    # ======================================

    def draw_ai_detections(
        self,
        frame,
        detections
    ):

        height, width = frame.shape[:2]

        for detection in detections:

            label = detection["label"]
            confidence = detection["confidence"]

            bbox = detection["bbox"]

            x1 = int(bbox["x1"])
            y1 = int(bbox["y1"])
            x2 = int(bbox["x2"])
            y2 = int(bbox["y2"])

            # Gioi han toa do trong anh
            x1 = max(0, min(x1, width - 1))
            x2 = max(0, min(x2, width - 1))

            y1 = max(0, min(y1, height - 1))
            y2 = max(0, min(y2, height - 1))

            if x2 <= x1 or y2 <= y1:
                continue

            color = self.ai_colors.get(
                label,
                (0, 255, 0)
            )

            # Ve khung phat hien
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            # Noi dung nhan
            text = (
                f"{label.upper()} "
                f"{confidence * 100:.1f}%"
            )

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            thickness = 1

            (tw, th), _ = cv2.getTextSize(
                text,
                font,
                font_scale,
                thickness
            )

            text_x = max(
                0,
                min(x1, width - tw - 12)
            )

            if y1 >= th + 12:
                label_top = y1 - th - 12
            else:
                label_top = y1

            label_bottom = min(
                height - 1,
                label_top + th + 12
            )

            # Nen mau cua nhan
            cv2.rectangle(
                frame,
                (text_x, label_top),
                (
                    min(width - 1, text_x + tw + 12),
                    label_bottom
                ),
                color,
                -1
            )

            # Chu trang
            cv2.putText(
                frame,
                text,
                (text_x + 6, label_bottom - 5),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )

        return frame

    # ======================================
    # 7. LUU ANH CHO CAC BAN GHI MOI
    # ======================================

    def save_detection_evidence(
        self,
        frame,
        session_id,
        detection_ids
    ):

        # Chi xu ly nhung ID vua duoc tao
        # boi DetectionHistoryService
        for detection_id in detection_ids:

            relative_path = None

            try:

                # ==========================
                # A. LUU ANH JPEG TREN O D
                # ==========================

                relative_path = (
                    evidence_service.save_snapshot(
                        frame,
                        session_id,
                        detection_id
                    )
                )

                # ==========================
                # B. CAP NHAT DUONG DAN SQLITE
                # ==========================

                conn = get_connection()

                try:

                    cursor = conn.execute(
                        """
                        UPDATE detections
                        SET snapshot_path = ?
                        WHERE detection_id = ?
                          AND session_id = ?
                          AND snapshot_path IS NULL
                        """,
                        (
                            relative_path,
                            detection_id,
                            session_id
                        )
                    )

                    if cursor.rowcount != 1:
                        raise RuntimeError(
                            "Khong tim thay detection can luu anh"
                        )

                    conn.commit()

                except Exception:

                    conn.rollback()
                    raise

                finally:

                    conn.close()

                print(
                    "DA LUU ANH BANG CHUNG:",
                    detection_id,
                    "|",
                    relative_path
                )

            except Exception as error:

                # Neu DB cap nhat that bai thi
                # xoa anh chua lien ket, neu co
                if relative_path is not None:

                    try:

                        image_path = (
                            evidence_service.get_snapshot_path(
                                relative_path
                            )
                        )

                        image_path.unlink()

                    except (
                        FileNotFoundError,
                        ValueError,
                        OSError
                    ):

                        pass

                # Khong dung video neu luu anh loi
                print(
                    "EVIDENCE SAVE ERROR:",
                    detection_id,
                    repr(error)
                )

    # ======================================
    # 8. TAO LUONG MJPEG
    # ======================================

    def generate_video_stream(
        self,
        session_id: str | None = None,
        ai_enabled: bool = False
    ):

        source = self.get_capture_source(session_id)

        is_camera = isinstance(source, int)

        cap = self.open_capture(source)

        ai_failed = False

        # Thoi diem kiem tra luu lich su
        last_history_check = 0.0

        try:

            if not cap.isOpened():
                raise RuntimeError(
                    "Cannot open video stream"
                )

            fps = cap.get(cv2.CAP_PROP_FPS)

            if fps <= 0 or fps > 120:
                fps = 15

            frame_delay = 1.0 / fps

            if ai_enabled:
                print("AI MONITORING STARTED")

            while True:

                success, frame = cap.read()

                if not success:

                    # Webcam bi ngat thi dung
                    if is_camera:

                        print(
                            "Webcam khong doc duoc frame!"
                        )

                        break

                    # File MP4 het thi phat lai
                    cap.set(
                        cv2.CAP_PROP_POS_FRAMES,
                        0
                    )

                    success, frame = cap.read()

                    if not success:
                        break

                # ==================================
                # 9. NHAN DIEN AI VA VE BOUNDING BOX
                # ==================================

                if ai_enabled and not ai_failed:

                    try:

                        # Goi YOLO11n
                        detections = detect_frame(frame)

                        # Ve khung len frame
                        frame = self.draw_ai_detections(
                            frame,
                            detections
                        )

                    except Exception as error:

                        ai_failed = True
                        detections = []

                        print(
                            "AI DETECTION ERROR:",
                            repr(error)
                        )

                    # ==================================
                    # 10. LUU LICH SU VA ANH BANG CHUNG
                    # ==================================

                    if (
                        not ai_failed
                        and session_id is not None
                        and detections
                    ):

                        now = time.monotonic()

                        # Khong truy van DB moi frame
                        if (
                            now - last_history_check
                            >= self.history_interval
                        ):

                            last_history_check = now

                            try:

                                session = (
                                    session_service.get_session_config(
                                        session_id
                                    )
                                )

                                # Chi luu khi phien RUNNING
                                if (
                                    session is not None
                                    and session["status"] == "RUNNING"
                                ):

                                    # A. Luu lich su vao SQLite
                                    result = (
                                        detection_history_service
                                        .save_detections(
                                            session_id,
                                            detections
                                        )
                                    )

                                    if result["saved"] > 0:

                                        print(
                                            "DA LUU PHAT HIEN:",
                                            session_id,
                                            "| So ban ghi:",
                                            result["saved"]
                                        )

                                        # B. Luu anh cho ban ghi moi
                                        self.save_detection_evidence(
                                            frame,
                                            session_id,
                                            result["detection_ids"]
                                        )

                            except Exception as db_error:

                                # DB loi thi van giu video
                                print(
                                    "DETECTION HISTORY ERROR:",
                                    repr(db_error)
                                )

                # ==================================
                # 11. HIEN THI TRANG THAI AI
                # ==================================

                if ai_enabled:

                    if ai_failed:

                        status_text = (
                            "AI ERROR - VIDEO ONLY"
                        )

                        status_color = (0, 0, 255)

                    else:

                        status_text = (
                            "AI ON - YOLO11n"
                        )

                        status_color = (0, 200, 0)

                    cv2.putText(
                        frame,
                        status_text,
                        (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        status_color,
                        2,
                        cv2.LINE_AA
                    )

                # ==================================
                # 12. MA HOA FRAME SANG MJPEG
                # ==================================

                encoded, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [
                        cv2.IMWRITE_JPEG_QUALITY,
                        75
                    ]
                )

                if not encoded:
                    continue

                frame_data = (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + buffer.tobytes()
                    + b"\r\n"
                )

                yield frame_data

                time.sleep(frame_delay)

        finally:

            cap.release()

            if ai_enabled:
                print(
                    "AI MONITORING STREAM CLOSED"
                )

    # ======================================
    # 13. GIAM SAT THEO TRANG THAI SESSION
    # ======================================

    def generate_monitoring_stream(
        self,
        session_id: str
    ):

        # Chi luong monitor moi bat YOLO
        video_generator = self.generate_video_stream(
            session_id,
            ai_enabled=True
        )

        try:

            for frame_data in video_generator:

                # Kiem tra trang thai phien
                session = (
                    session_service.get_session_config(
                        session_id
                    )
                )

                if session is None:
                    break

                if session["status"] != "RUNNING":
                    break

                yield frame_data

        finally:

            video_generator.close()


# ==========================================
# DOI TUONG DUNG CHUNG
# ==========================================

video_service = VideoService()
