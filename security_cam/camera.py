from __future__ import annotations

import cv2


class CameraError(RuntimeError):
    pass


class Camera:
    def __init__(self, index: int = 0) -> None:
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            self.cap.release()
            raise CameraError(
                "Could not open camera. Check that a webcam is connected and not in use."
            )

    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            raise CameraError("Failed to read from camera. Exiting.")
        return frame

    @property
    def frame_size(self) -> tuple[int, int]:
        return (int(self.cap.get(3)), int(self.cap.get(4)))

    def fps(self, fallback: float = 20.0) -> float:
        value = float(self.cap.get(cv2.CAP_PROP_FPS) or 0)
        return value if value >= 1 else fallback

    def release(self) -> None:
        self.cap.release()
