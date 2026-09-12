from __future__ import annotations

import datetime
import os
from collections import deque

import cv2


class PreRollBuffer:
    """Keep the last N seconds of frames so clips include the lead-in to an event."""

    def __init__(self, seconds: float, fps: float) -> None:
        if seconds < 0:
            raise ValueError("preroll seconds must be >= 0")
        if fps <= 0:
            raise ValueError("fps must be > 0")
        self.seconds = seconds
        self.fps = fps
        maxlen = int(round(seconds * fps)) if seconds > 0 else 0
        self._frames: deque = deque(maxlen=maxlen)

    @property
    def maxlen(self) -> int:
        return self._frames.maxlen or 0

    def append(self, frame) -> None:
        if self.maxlen == 0:
            return
        self._frames.append(frame.copy())

    def snapshot(self) -> list:
        return list(self._frames)

    def __len__(self) -> int:
        return len(self._frames)


class ClipRecorder:
    """OpenCV VideoWriter wrapper that can flush a pre-roll buffer on start."""

    def __init__(
        self,
        output_dir: str,
        frame_size: tuple[int, int],
        fps: float,
        fourcc: str = "mp4v",
    ) -> None:
        self.output_dir = output_dir
        self.frame_size = frame_size
        self.fps = fps
        self._fourcc = cv2.VideoWriter_fourcc(*fourcc)
        self._writer: cv2.VideoWriter | None = None
        self.path: str | None = None

    @property
    def is_recording(self) -> bool:
        return self._writer is not None

    def start(self, preroll_frames, timestamp: str | None = None) -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        stamp = timestamp or datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        self.path = os.path.join(self.output_dir, f"{stamp}.mp4")
        self._writer = cv2.VideoWriter(self.path, self._fourcc, self.fps, self.frame_size)
        if not self._writer.isOpened():
            self._writer = None
            raise RuntimeError(f"Could not open VideoWriter for {self.path}")
        for frame in preroll_frames:
            self._writer.write(frame)
        return self.path

    def write(self, frame) -> None:
        if self._writer is not None:
            self._writer.write(frame)

    def stop(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None
