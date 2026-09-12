from __future__ import annotations

import types
import unittest
from unittest.mock import patch

import numpy as np

from security_cam.detector import (
    DetectionResult,
    PersonDetector,
    interpret_pose_result,
    pose_confidence,
)


def _landmark(score: float):
    return types.SimpleNamespace(visibility=score, presence=score)


def _pose(*scores: float):
    # Pad to include hip landmarks (index 24).
    values = list(scores)
    while len(values) < 25:
        values.append(0.0)
    return [_landmark(v) for v in values]


class InterpretTests(unittest.TestCase):
    def test_empty_result_is_not_a_person(self):
        raw = types.SimpleNamespace(pose_landmarks=[])
        result = interpret_pose_result(raw, 0.5)
        self.assertEqual(result, DetectionResult(False, 0.0))

    def test_confident_torso_is_a_person(self):
        pose = _pose()
        for index in (0, 11, 12, 23, 24):
            pose[index] = _landmark(0.9)
        raw = types.SimpleNamespace(pose_landmarks=[pose])
        result = interpret_pose_result(raw, 0.5)
        self.assertTrue(result.found)
        self.assertGreaterEqual(result.confidence, 0.9)

    def test_low_confidence_rejected(self):
        pose = _pose()
        for index in (0, 11, 12, 23, 24):
            pose[index] = _landmark(0.2)
        raw = types.SimpleNamespace(pose_landmarks=[pose])
        result = interpret_pose_result(raw, 0.5)
        self.assertFalse(result.found)
        self.assertAlmostEqual(result.confidence, 0.2)

    def test_pose_confidence_uses_key_landmarks(self):
        pose = _pose()
        pose[0] = _landmark(1.0)
        pose[11] = _landmark(1.0)
        pose[12] = _landmark(0.0)
        pose[23] = _landmark(0.0)
        pose[24] = _landmark(0.0)
        self.assertAlmostEqual(pose_confidence(pose), 0.4)


class PersonDetectorTests(unittest.TestCase):
    def test_detect_uses_injected_backend_without_mediapipe(self):
        pose = _pose()
        for index in (0, 11, 12, 23, 24):
            pose[index] = _landmark(0.8)
        infer = lambda _frame: types.SimpleNamespace(pose_landmarks=[pose])
        detector = PersonDetector(min_confidence=0.5, infer_fn=infer)
        frame = np.zeros((16, 16, 3), dtype=np.uint8)
        result = detector.detect(frame)
        self.assertTrue(result.found)
        detector.close()

    def test_blank_frame_via_empty_infer(self):
        detector = PersonDetector(
            infer_fn=lambda _frame: types.SimpleNamespace(pose_landmarks=[])
        )
        result = detector.detect(np.zeros((8, 8, 3), dtype=np.uint8))
        self.assertFalse(result.found)

    def test_ensure_model_skips_download_when_file_exists(self):
        from security_cam.detector import ensure_pose_model

        with patch("security_cam.detector.urllib.request.urlretrieve") as retrieve:
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "pose_landmarker_lite.task"
                path.write_bytes(b"model")
                resolved = ensure_pose_model(path)
                self.assertEqual(resolved, path)
                retrieve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
