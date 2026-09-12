from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from security_cam.recorder import ClipRecorder, PreRollBuffer


class PreRollBufferTests(unittest.TestCase):
    def test_keeps_only_maxlen_frames(self):
        buffer = PreRollBuffer(seconds=0.15, fps=20)
        self.assertEqual(buffer.maxlen, 3)
        for i in range(5):
            buffer.append(np.full((4, 4, 3), i, dtype=np.uint8))
        frames = buffer.snapshot()
        self.assertEqual(len(frames), 3)
        self.assertEqual(int(frames[0][0, 0, 0]), 2)
        self.assertEqual(int(frames[-1][0, 0, 0]), 4)

    def test_copies_frames_so_later_mutation_is_safe(self):
        buffer = PreRollBuffer(seconds=1, fps=1)
        frame = np.zeros((2, 2, 3), dtype=np.uint8)
        buffer.append(frame)
        frame[:] = 9
        self.assertEqual(int(buffer.snapshot()[0][0, 0, 0]), 0)

    def test_zero_seconds_stores_nothing(self):
        buffer = PreRollBuffer(seconds=0, fps=20)
        buffer.append(np.zeros((2, 2, 3), dtype=np.uint8))
        self.assertEqual(len(buffer), 0)

    def test_rejects_negative_seconds(self):
        with self.assertRaises(ValueError):
            PreRollBuffer(seconds=-1, fps=20)


class ClipRecorderTests(unittest.TestCase):
    def test_start_flushes_preroll_then_write_appends(self):
        preroll = [np.zeros((8, 8, 3), dtype=np.uint8) for _ in range(3)]
        live = np.ones((8, 8, 3), dtype=np.uint8)
        written = []

        fake_writer = MagicMock()
        fake_writer.isOpened.return_value = True
        fake_writer.write.side_effect = lambda frame: written.append(frame.copy())

        with tempfile.TemporaryDirectory() as tmp:
            recorder = ClipRecorder(tmp, (8, 8), 20.0)
            with patch("security_cam.recorder.cv2.VideoWriter", return_value=fake_writer):
                path = recorder.start(preroll, timestamp="clip")
                recorder.write(live)
                recorder.stop()

            self.assertTrue(path.endswith("clip.mp4"))
            self.assertEqual(len(written), 4)
            self.assertTrue(np.array_equal(written[0], preroll[0]))
            self.assertTrue(np.array_equal(written[-1], live))
            self.assertFalse(recorder.is_recording)

    def test_creates_output_directory(self):
        fake_writer = MagicMock()
        fake_writer.isOpened.return_value = True
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "clips", "nested")
            recorder = ClipRecorder(out, (8, 8), 20.0)
            with patch("security_cam.recorder.cv2.VideoWriter", return_value=fake_writer):
                recorder.start([], timestamp="x")
                recorder.stop()
            self.assertTrue(os.path.isdir(out))


if __name__ == "__main__":
    unittest.main()
