# Security Camera (Intruder Alert)

Laptop-webcam security camera that uses OpenCV Haar cascades to detect faces and bodies. When a person is detected it starts recording an MP4 clip and sends a WhatsApp alert through Twilio.

## Requirements

- Python 3.10+
- A webcam
- A [Twilio](https://www.twilio.com/) account with WhatsApp (sandbox is fine for testing)

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your Twilio credentials. Never commit `.env`.

## Environment variables

| Variable | Description |
| --- | --- |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_WHATSAPP_TO` | Destination, e.g. `whatsapp:+15555555555` |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp sender, e.g. `whatsapp:+14155238886` (sandbox) |
| `ALERT_COOLDOWN_SECONDS` | Minimum seconds between WhatsApp alerts (default `60`) |

## Run

```bash
python security.py
```

- A camera window opens. Press `q` to quit.
- Detection starts recording `DD-MM-YYYY-HH-MM-SS.mp4` in the project directory.
- Recording stops about 5 seconds after faces/bodies leave the frame.
- Camera open/read failures exit with a message instead of crashing.
- WhatsApp alerts are rate-limited by `ALERT_COOLDOWN_SECONDS` so brief flicker does not spam.

## Dependencies

Pinned in `requirements.txt`:

- opencv-python 4.14.0.94
- twilio 9.11.0
- python-dotenv 1.2.3
