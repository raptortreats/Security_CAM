from __future__ import annotations

import subprocess
import sys
import unittest


class EntryPointTests(unittest.TestCase):
    def test_security_py_help_without_twilio_or_camera(self):
        result = subprocess.run(
            [sys.executable, "security.py", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--local-only", result.stdout)
        self.assertIn("--preroll", result.stdout)

    def test_module_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "security_cam", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("MediaPipe", result.stdout)


if __name__ == "__main__":
    unittest.main()
