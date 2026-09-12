from __future__ import annotations

import os
from dataclasses import dataclass

TWILIO_ENV_KEYS = (
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_WHATSAPP_TO",
    "TWILIO_WHATSAPP_FROM",
)

TRUE_FLAGS = {"1", "true", "yes", "on"}


def env_flag(name: str, default: bool = False, environ: dict[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    raw = env.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_FLAGS


def env_value(name: str, default: str | None = None, environ: dict[str, str] | None = None) -> str | None:
    env = environ if environ is not None else os.environ
    raw = env.get(name)
    if raw is None or raw == "":
        return default
    return raw


@dataclass(frozen=True)
class Settings:
    camera_index: int = 0
    confidence: float = 0.5
    alert_cooldown_seconds: float = 60.0
    preroll_seconds: float = 3.0
    stop_delay_seconds: float = 5.0
    output_dir: str = "."
    local_only: bool = False
    preview: bool = True
    fps_fallback: float = 20.0
    model_path: str | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_to: str | None = None
    twilio_whatsapp_from: str | None = None

    def missing_twilio(self) -> list[str]:
        required = {
            "TWILIO_ACCOUNT_SID": self.twilio_account_sid,
            "TWILIO_AUTH_TOKEN": self.twilio_auth_token,
            "TWILIO_WHATSAPP_TO": self.twilio_whatsapp_to,
            "TWILIO_WHATSAPP_FROM": self.twilio_whatsapp_from,
        }
        return [name for name, value in required.items() if not value]


def settings_from_sources(
    *,
    camera: int | None = None,
    confidence: float | None = None,
    cooldown: float | None = None,
    preroll: float | None = None,
    output_dir: str | None = None,
    local_only: bool = False,
    preview: bool = True,
    model_path: str | None = None,
    environ: dict[str, str] | None = None,
) -> Settings:
    env = environ if environ is not None else os.environ
    local = local_only or env_flag("LOCAL_ONLY", False, env)

    return Settings(
        camera_index=_int(camera, env_value("CAMERA_INDEX", "0", env), 0),
        confidence=_float(confidence, env_value("DETECTION_CONFIDENCE", "0.5", env), 0.5),
        alert_cooldown_seconds=_float(
            cooldown, env_value("ALERT_COOLDOWN_SECONDS", "60", env), 60.0
        ),
        preroll_seconds=_float(preroll, env_value("PREROLL_SECONDS", "3", env), 3.0),
        stop_delay_seconds=_float(None, env_value("STOP_DELAY_SECONDS", "5", env), 5.0),
        output_dir=output_dir or env_value("OUTPUT_DIR", ".", env) or ".",
        local_only=local,
        preview=preview,
        fps_fallback=_float(None, env_value("FPS_FALLBACK", "20", env), 20.0),
        model_path=model_path or env_value("MODEL_PATH", None, env),
        twilio_account_sid=env_value("TWILIO_ACCOUNT_SID", None, env),
        twilio_auth_token=env_value("TWILIO_AUTH_TOKEN", None, env),
        twilio_whatsapp_to=env_value("TWILIO_WHATSAPP_TO", None, env),
        twilio_whatsapp_from=env_value("TWILIO_WHATSAPP_FROM", None, env),
    )


def _int(cli_value: int | None, env_raw: str | None, default: int) -> int:
    if cli_value is not None:
        return int(cli_value)
    if env_raw is None or env_raw == "":
        return default
    return int(env_raw)


def _float(cli_value: float | None, env_raw: str | None, default: float) -> float:
    if cli_value is not None:
        return float(cli_value)
    if env_raw is None or env_raw == "":
        return default
    return float(env_raw)
