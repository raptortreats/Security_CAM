from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from security_cam.cli import build_parser, load_settings, parse_args, validate_settings
from security_cam.config import Settings


class CliHelpTests(unittest.TestCase):
    def test_help_lists_v2_flags(self):
        parser = build_parser()
        buf = io.StringIO()
        with self.assertRaises(SystemExit) as raised, redirect_stdout(buf):
            parser.parse_args(["--help"])
        self.assertEqual(raised.exception.code, 0)
        help_text = buf.getvalue()
        for flag in (
            "--camera",
            "--confidence",
            "--cooldown",
            "--preroll",
            "--output-dir",
            "--local-only",
            "--no-preview",
            "--model-path",
        ):
            self.assertIn(flag, help_text)

    def test_parse_local_only(self):
        args = parse_args(["--local-only", "--preroll", "4", "--camera", "2"])
        self.assertTrue(args.local_only)
        self.assertEqual(args.preroll, 4.0)
        self.assertEqual(args.camera, 2)


class SettingsTests(unittest.TestCase):
    def test_cli_overrides_env(self):
        environ = {
            "CAMERA_INDEX": "9",
            "DETECTION_CONFIDENCE": "0.1",
            "ALERT_COOLDOWN_SECONDS": "10",
            "PREROLL_SECONDS": "2",
            "OUTPUT_DIR": "from-env",
        }
        with patch("security_cam.cli.load_dotenv"):
            settings = load_settings(
                [
                    "--camera",
                    "1",
                    "--confidence",
                    "0.8",
                    "--cooldown",
                    "90",
                    "--preroll",
                    "5",
                    "--output-dir",
                    "clips",
                    "--local-only",
                ],
                environ=environ,
            )
        self.assertEqual(settings.camera_index, 1)
        self.assertEqual(settings.confidence, 0.8)
        self.assertEqual(settings.alert_cooldown_seconds, 90.0)
        self.assertEqual(settings.preroll_seconds, 5.0)
        self.assertEqual(settings.output_dir, "clips")
        self.assertTrue(settings.local_only)

    def test_env_defaults_and_local_only_flag(self):
        environ = {
            "LOCAL_ONLY": "true",
            "CAMERA_INDEX": "3",
            "PREROLL_SECONDS": "2.5",
        }
        with patch("security_cam.cli.load_dotenv"):
            settings = load_settings([], environ=environ)
        self.assertTrue(settings.local_only)
        self.assertEqual(settings.camera_index, 3)
        self.assertEqual(settings.preroll_seconds, 2.5)

    def test_local_only_skips_twilio_validation(self):
        settings = Settings(local_only=True)
        validate_settings(settings)

    def test_missing_twilio_exits_unless_local_only(self):
        settings = Settings(local_only=False)
        with self.assertRaises(SystemExit) as raised:
            validate_settings(settings)
        self.assertIn("TWILIO_ACCOUNT_SID", str(raised.exception))
        self.assertIn("--local-only", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
