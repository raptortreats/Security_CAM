import datetime
import os
import sys
import time

import cv2
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
ALERT_COOLDOWN_SECONDS = float(os.getenv("ALERT_COOLDOWN_SECONDS", "60"))

required_env = {
    "TWILIO_ACCOUNT_SID": TWILIO_ACCOUNT_SID,
    "TWILIO_AUTH_TOKEN": TWILIO_AUTH_TOKEN,
    "TWILIO_WHATSAPP_TO": TWILIO_WHATSAPP_TO,
    "TWILIO_WHATSAPP_FROM": TWILIO_WHATSAPP_FROM,
}
missing = [name for name, value in required_env.items() if not value]
if missing:
    sys.exit(
        "Missing required environment variables: "
        + ", ".join(missing)
        + ". Copy .env.example to .env and fill in your values."
    )

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
last_alert_time = 0.0


def send_alert():
    global last_alert_time
    now = time.time()
    if now - last_alert_time < ALERT_COOLDOWN_SECONDS:
        return
    client.messages.create(
        to=TWILIO_WHATSAPP_TO,
        from_=TWILIO_WHATSAPP_FROM,
        body="Intruder Alert",
    )
    last_alert_time = now


watcher = cv2.VideoCapture(0)
if not watcher.isOpened():
    watcher.release()
    sys.exit("Could not open camera. Check that a webcam is connected and not in use.")

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
body_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_fullbody.xml"
)

detection = False
detection_stopped_time = None
timer_started = False
out = None

frame_size = (int(watcher.get(3)), int(watcher.get(4)))
fourcc = cv2.VideoWriter_fourcc(*"mp4v")

while True:
    ret, frame = watcher.read()
    if not ret:
        print("Failed to read from camera. Exiting.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    faces = face_cascade.detectMultiScale(blur, 1.3, 5)
    bodies = body_cascade.detectMultiScale(blur, 1.3, 5)

    if len(faces) + len(bodies) > 0:
        if detection:
            timer_started = False
        else:
            detection = True
            send_alert()
            current_time = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
            out = cv2.VideoWriter(
                f"{current_time}.mp4", fourcc, 20, frame_size
            )
            print("Started Recording!")
    elif detection:
        if timer_started:
            if time.time() - detection_stopped_time >= 5:
                detection = False
                timer_started = False
                if out is not None:
                    out.release()
                    out = None
                print("Stop Recording!")
        else:
            timer_started = True
            detection_stopped_time = time.time()

    if detection and out is not None:
        out.write(frame)

    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) == ord("q"):
        break

if out is not None:
    out.release()
watcher.release()
cv2.destroyAllWindows()
