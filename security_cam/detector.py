from __future__ import annotations

import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# MediaPipe Pose Landmarker lite — person presence from body landmarks.
# Face/Hands tasks need a visible face or close-up gestures; pose still fires
# when someone is turned away or only partially in frame.
POSE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)
POSE_MODEL_NAME = "pose_landmarker_lite.task"

# Nose, shoulders, hips — enough to decide "a person is in the room".
_KEY_LANDMARKS = (0, 11, 12, 23, 24)


@dataclass(frozen=True)
class DetectionResult:
    found: bool
    confidence: float


def bundled_model_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "models"


def default_model_path() -> Path:
    bundled = bundled_model_dir() / POSE_MODEL_NAME
    if bundled.is_file():
        return bundled
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return cache / "security_cam" / POSE_MODEL_NAME


def ensure_pose_model(model_path: str | Path | None = None) -> Path:
    path = Path(model_path) if model_path else default_model_path()
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading MediaPipe Pose Landmarker to {path} ...")
    try:
        urllib.request.urlretrieve(POSE_MODEL_URL, path)
    except Exception as exc:
        if path.exists():
            path.unlink(missing_ok=True)
        raise RuntimeError(
            "Could not download the Pose Landmarker model. "
            f"Save {POSE_MODEL_NAME} to {path} or pass --model-path. "
            f"Source: {POSE_MODEL_URL}"
        ) from exc
    return path


def landmark_score(landmark: Any) -> float:
    visibility = float(getattr(landmark, "visibility", 0.0) or 0.0)
    presence = float(getattr(landmark, "presence", 0.0) or 0.0)
    return max(visibility, presence)


def pose_confidence(landmarks: Any) -> float:
    if not landmarks:
        return 0.0
    scores = []
    for index in _KEY_LANDMARKS:
        if index < len(landmarks):
            scores.append(landmark_score(landmarks[index]))
    if not scores:
        scores = [landmark_score(item) for item in landmarks]
    return sum(scores) / len(scores) if scores else 0.0


def interpret_pose_result(raw: Any, min_confidence: float) -> DetectionResult:
    poses = getattr(raw, "pose_landmarks", None) or []
    if not poses:
        return DetectionResult(False, 0.0)
    confidence = pose_confidence(poses[0])
    return DetectionResult(confidence >= min_confidence, confidence)


class PersonDetector:
    """Detect a person with MediaPipe Pose Landmarker (Tasks API)."""

    def __init__(
        self,
        min_confidence: float = 0.5,
        model_path: str | Path | None = None,
        infer_fn: Callable[..., Any] | None = None,
    ) -> None:
        self.min_confidence = min_confidence
        self._infer_fn = infer_fn
        self._landmarker = None
        self._timestamp_ms = 0
        if infer_fn is None:
            self._landmarker = self._create_landmarker(model_path)

    def _create_landmarker(self, model_path: str | Path | None):
        import mediapipe as mp

        resolved = ensure_pose_model(model_path)
        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(resolved)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=self.min_confidence,
            min_pose_presence_confidence=self.min_confidence,
            min_tracking_confidence=self.min_confidence,
        )
        return mp.tasks.vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame_bgr, timestamp_ms: int | None = None) -> DetectionResult:
        raw = self._infer(frame_bgr, timestamp_ms)
        return interpret_pose_result(raw, self.min_confidence)

    def _infer(self, frame_bgr, timestamp_ms: int | None):
        if self._infer_fn is not None:
            return self._infer_fn(frame_bgr)
        import cv2
        import mediapipe as mp
        import numpy as np

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        if not rgb.flags["C_CONTIGUOUS"]:
            rgb = np.ascontiguousarray(rgb)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = timestamp_ms if timestamp_ms is not None else self._next_timestamp()
        return self._landmarker.detect_for_video(image, ts)

    def _next_timestamp(self) -> int:
        self._timestamp_ms += 50
        return self._timestamp_ms

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

    def __enter__(self) -> PersonDetector:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
