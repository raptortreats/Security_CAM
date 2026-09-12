from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from security_cam.config import Settings, settings_from_sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="security.py",
        description=(
            "Laptop webcam security camera. Detects a person with MediaPipe Pose "
            "Landmarker, records an MP4 with a short pre-roll, and optionally "
            "sends a Twilio WhatsApp alert."
        ),
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=None,
        metavar="INDEX",
        help="Camera device index (env CAMERA_INDEX, default 0).",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=None,
        metavar="SCORE",
        help="Minimum pose detection confidence 0-1 (env DETECTION_CONFIDENCE, default 0.5).",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Minimum seconds between WhatsApp alerts (env ALERT_COOLDOWN_SECONDS, default 60).",
    )
    parser.add_argument(
        "--preroll",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Seconds of frames kept before detection (env PREROLL_SECONDS, default 3, recommend 2-5).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help="Directory for recorded MP4 clips (env OUTPUT_DIR, default current directory).",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Record clips without WhatsApp. Twilio env vars are not required.",
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Do not open the OpenCV preview window.",
    )
    parser.add_argument(
        "--model-path",
        default=None,
        metavar="PATH",
        help="Path to pose_landmarker_lite.task (env MODEL_PATH). Downloaded on first run if missing.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def load_settings(argv: list[str] | None = None, environ: dict[str, str] | None = None) -> Settings:
    load_dotenv()
    args = parse_args(argv)
    return settings_from_sources(
        camera=args.camera,
        confidence=args.confidence,
        cooldown=args.cooldown,
        preroll=args.preroll,
        output_dir=args.output_dir,
        local_only=args.local_only,
        preview=not args.no_preview,
        model_path=args.model_path,
        environ=environ,
    )


def validate_settings(settings: Settings) -> None:
    if settings.preroll_seconds < 0:
        sys.exit("preroll seconds must be >= 0")
    if not 0.0 <= settings.confidence <= 1.0:
        sys.exit("confidence must be between 0 and 1")
    if settings.local_only:
        return
    missing = settings.missing_twilio()
    if missing:
        sys.exit(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in your values, or pass --local-only."
        )


def main(argv: list[str] | None = None) -> None:
    from security_cam.app import run

    settings = load_settings(argv)
    validate_settings(settings)
    run(settings)
