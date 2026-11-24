
# ==========================================
# BUOC 9.11C - TEST LUU ANH BANG CHUNG
# ==========================================

import cv2

from backend.services.evidence_service import (
    evidence_service
)


def main():

    # Ma gia lap, khong ghi vao SQLite
    session_id = "TEST_EVIDENCE"
    detection_id = 999999

    # Lay video mau tren o D
    video_path = (
        evidence_service.project_root
        / "data"
        / "videos"
        / "test.mp4"
    )

    print("===== KIEM TRA EVIDENCE SERVICE =====")
    print("Video:", video_path)

    cap = cv2.VideoCapture(str(video_path))

    # Duong dan anh test de don dep
    test_folder = (
        evidence_service.evidence_dir
        / session_id
    )

    test_image = (
        test_folder
        / f"detection_{detection_id}.jpg"
    )

    try:

        # ==================================
        # 1. DOC FRAME TU VIDEO
        # ==================================

        if not cap.isOpened():
            raise RuntimeError(
                "Khong mo duoc video test.mp4"
            )

        success, frame = cap.read()

        if not success:
            raise RuntimeError(
                "Khong doc duoc frame"
            )

        print("\nDOC VIDEO: THANH CONG")
        print("Kich thuoc frame:", frame.shape)

        # Ghi chu de phan biet anh test
        cv2.putText(
            frame,
            "EVIDENCE TEST",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # ==================================
        # 2. LUU ANH JPEG
        # ==================================

        relative_path = (
            evidence_service.save_snapshot(
                frame,
                session_id,
                detection_id
            )
        )

        print("\nLUU ANH: THANH CONG")
        print("Duong dan SQLite:", relative_path)

        # ==================================
        # 3. KIEM TRA ANH DA LUU
        # ==================================

        image_path = (
            evidence_service.get_snapshot_path(
                relative_path
            )
        )

        print("Duong dan that:", image_path)

        if not image_path.is_file():
            raise RuntimeError(
                "Anh khong ton tai"
            )

        # ==================================
        # 4. DOC LAI ANH JPEG
        # ==================================

        saved_frame = cv2.imread(
            str(image_path)
        )

        if saved_frame is None:
            raise RuntimeError(
                "Khong doc duoc anh da luu"
            )

        if saved_frame.shape != frame.shape:
            raise RuntimeError(
                "Kich thuoc anh khong khop"
            )

        print("\nDOC LAI ANH: THANH CONG")

        print(
            "Dung luong:",
            image_path.stat().st_size,
            "bytes"
        )

        print("\n===== KET QUA =====")
        print("EVIDENCE SERVICE: PASS")
        print("LUU JPEG: PASS")
        print("DOC JPEG: PASS")
        print("DUONG DAN O D: PASS")

    finally:

        # Giai phong video
        cap.release()

        # ==================================
        # 5. DON DEP ANH THU NGHIEM
        # ==================================

        if test_image.exists():
            test_image.unlink()

        if (
            test_folder.exists()
            and not any(test_folder.iterdir())
        ):
            test_folder.rmdir()

        print("\nDA DON DEP ANH TEST!")


if __name__ == "__main__":
    main()
