
# ==========================================
# EVIDENCE SERVICE
# LUU ANH BANG CHUNG KHI AI PHAT HIEN VU KHI
# ==========================================

import re
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np


class EvidenceService:

    def __init__(self):

        # Thu muc goc du an tren o D
        self.project_root = (
            Path(__file__).resolve().parents[2]
        )

        # Thu muc luu anh bang chung
        self.evidence_dir = (
            self.project_root
            / "data"
            / "evidence"
        )

        # Chat luong anh JPEG: 80%
        self.jpeg_quality = 80

    # ======================================
    # 1. KIEM TRA MA PHIEN
    # ======================================

    def validate_session_id(self, session_id):

        if not isinstance(session_id, str):
            raise ValueError(
                "Session ID khong hop le"
            )

        session_id = session_id.strip()

        # Ngan duong dan nguy hiem
        if not re.fullmatch(
            r"[A-Za-z0-9_-]{1,100}",
            session_id
        ):
            raise ValueError(
                "Session ID chua ky tu khong hop le"
            )

        return session_id

    # ======================================
    # 2. LUU ANH BANG CHUNG
    # ======================================

    def save_snapshot(
        self,
        frame,
        session_id,
        detection_id
    ):

        # Kiem tra session_id
        session_id = self.validate_session_id(
            session_id
        )

        # Kiem tra detection_id
        if (
            not isinstance(detection_id, int)
            or isinstance(detection_id, bool)
            or detection_id <= 0
        ):
            raise ValueError(
                "Detection ID khong hop le"
            )

        # Kiem tra khung hinh OpenCV
        if (
            not isinstance(frame, np.ndarray)
            or frame.size == 0
            or frame.ndim != 3
            or frame.shape[2] != 3
        ):
            raise ValueError(
                "Frame khong hop le"
            )

        # ==================================
        # 3. TAO THU MUC THEO PHIEN
        # ==================================

        session_folder = (
            self.evidence_dir / session_id
        )

        session_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # Ten anh theo ma ban ghi SQLite
        filename = (
            f"detection_{detection_id}.jpg"
        )

        image_path = (
            session_folder / filename
        )

        # ==================================
        # 4. MA HOA FRAME SANG JPEG
        # ==================================

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                self.jpeg_quality
            ]
        )

        if not success:
            raise RuntimeError(
                "Khong the ma hoa anh JPEG"
            )

        # ==================================
        # 5. LUU ANH TREN O D
        # ==================================

        # Publish a complete JPEG; readers never see a partly written image.
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=session_folder, suffix=".tmp", delete=False) as output:
                temporary_path = Path(output.name)
                output.write(buffer.tobytes())
            os.replace(temporary_path, image_path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        # Duong dan tuong doi de luu SQLite
        relative_path = (
            image_path.relative_to(
                self.project_root
            ).as_posix()
        )

        return relative_path

    # ======================================
    # 6. TIM ANH BANG CHUNG
    # ======================================

    def get_snapshot_path(
        self,
        relative_path
    ):

        if not isinstance(relative_path, str):
            raise ValueError(
                "Duong dan anh khong hop le"
            )

        # Chuyen duong dan DB thanh duong dan that
        image_path = (
            self.project_root / relative_path
        ).resolve()

        allowed_folder = (
            self.evidence_dir
        ).resolve()

        # Chi doc anh ben trong data/evidence
        if not image_path.is_relative_to(
            allowed_folder
        ):
            raise ValueError(
                "Duong dan anh nam ngoai evidence"
            )

        if not image_path.is_file():
            raise FileNotFoundError(
                "Khong tim thay anh bang chung"
            )

        return image_path


# ==========================================
# DOI TUONG DUNG CHUNG CHO BACKEND
# ==========================================

evidence_service = EvidenceService()
