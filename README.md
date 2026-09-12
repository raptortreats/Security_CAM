# Security Camera v2 (Intruder Alert)

Laptop-webcam security camera. When a person is detected it starts recording an MP4 clip (including a short pre-roll) and can send a WhatsApp alert through Twilio.

## Detector choice (v2)

v1 used OpenCV Haar cascades (`haarcascade_frontalface_default` and `haarcascade_fullbody`). Those miss people who are not facing the camera, and the full-body cascade is unreliable at typical webcam distances.

v2 uses **MediaPipe Pose Landmarker (lite)** via the current Tasks API:

- Pose is the right signal for an “intruder”: it looks for a body (shoulders, hips, and other landmarks), including side/back views.
- MediaPipe **Face** is better for a close, facing subject. **Hands** is for gestures. Neither is enough on its own for room-scale presence.
- **OpenCV** is still used for webcam capture, the preview window, and MP4 writing.

The lite `.task` model is downloaded on first run (or you can pass `--model-path`).

## Requirements

- Python 3.10+
- A webcam
- Optional: a [Twilio](https://www.twilio.com/) account with WhatsApp (sandbox is fine). Not needed for `--local-only`.
- Linux: MediaPipe 1.0 needs OpenGL/EGL (`sudo apt install libegl1` if import fails). Desktop installs usually already have this.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your Twilio credentials if you want WhatsApp alerts. Never commit `.env`.

## Run

```bash
python security.py
# or
python -m security_cam
```

Local recording only (no Twilio, no WhatsApp):

```bash
python security.py --local-only --output-dir recordings --preroll 3
```

- A camera window opens unless you pass `--no-preview` (use that on headless machines). Press `q` to quit.
- Detection writes `DD-MM-YYYY-HH-MM-SS.mp4` under `--output-dir` (default: current directory).
- Clips include about `--preroll` seconds of frames from *before* the person appeared (default 3s, recommend 2–5).
- Recording stops about 5 seconds after the person leaves the frame.
- Camera open/read failures exit with a message instead of crashing.
- WhatsApp alerts are rate-limited by `--cooldown` / `ALERT_COOLDOWN_SECONDS` so brief flicker does not spam.

## CLI flags

| Flag | Env var | Default | Description |
| --- | --- | --- | --- |
| `--camera INDEX` | `CAMERA_INDEX` | `0` | Webcam device index |
| `--confidence SCORE` | `DETECTION_CONFIDENCE` | `0.5` | Minimum pose detection confidence (0–1) |
| `--cooldown SECONDS` | `ALERT_COOLDOWN_SECONDS` | `60` | Minimum seconds between WhatsApp alerts |
| `--preroll SECONDS` | `PREROLL_SECONDS` | `3` | Pre-roll buffer length (recommend 2–5) |
| `--output-dir DIR` | `OUTPUT_DIR` | `.` | Directory for MP4 clips |
| `--local-only` | `LOCAL_ONLY=true` | off | Record without WhatsApp; Twilio vars not required |
| `--no-preview` | — | off | Skip the OpenCV window |
| `--model-path PATH` | `MODEL_PATH` | auto | `pose_landmarker_lite.task` (downloaded if missing) |

CLI flags override `.env` / environment variables.

```bash
python security.py --help
```

## Environment variables

| Variable | Description |
| --- | --- |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID (required unless `--local-only`) |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_WHATSAPP_TO` | Destination, e.g. `whatsapp:+15555555555` |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp sender, e.g. `whatsapp:+14155238886` (sandbox) |
| `ALERT_COOLDOWN_SECONDS` | Minimum seconds between WhatsApp alerts (default `60`) |
| `CAMERA_INDEX` | Webcam index (default `0`) |
| `DETECTION_CONFIDENCE` | Pose confidence threshold (default `0.5`) |
| `PREROLL_SECONDS` | Pre-roll seconds (default `3`) |
| `OUTPUT_DIR` | Clip directory (default `.`) |
| `LOCAL_ONLY` | `true` / `1` to disable WhatsApp |
| `MODEL_PATH` | Optional path to the Pose Landmarker `.task` file |
| `STOP_DELAY_SECONDS` | Seconds to keep recording after the person leaves (default `5`) |

## Tests

No webcam required:

```bash
python -m unittest discover -s tests -v
```

Covers the pre-roll buffer, CLI help/flags, local-only alerts without Twilio, cooldown, and mocked pose results.

## Layout

```
security.py            # python security.py
security_cam/
  cli.py               # argparse
  config.py            # CLI + .env settings
  camera.py            # OpenCV capture
  detector.py          # MediaPipe Pose Landmarker
  recorder.py          # pre-roll buffer + VideoWriter
  alerts.py            # Twilio WhatsApp or local-only
  app.py               # main loop
```

## Dependencies

Pinned in `requirements.txt`:

- mediapipe 1.0.1 (Pose Landmarker Tasks API)
- opencv-contrib-python 4.14.0.94 (capture, preview, recording; pulled/aligned with MediaPipe)
- twilio 9.11.0
- python-dotenv 1.2.3
