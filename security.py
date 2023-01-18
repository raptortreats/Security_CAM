import cv2
import time
import datetime

#this below snippet is to notify through whatsapp
import twilio
from twilio.rest import Client
account_sid = 'ACcc1f5e63748d3809fb569f3710227bbe'
auth_token = 'ccc2c112d48d4e01b6a80a0569d48413'
client = Client(account_sid, auth_token)
def msg():
    message = client.messages.create(to = 'whatsapp:+918106833102',
                                    from_ = 'whatsapp:+14155238886',
                                    body = 'Intruder Alert')
    return

watcher = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
body_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_fullbody.xml")

detection = False
detection_stopped_time = None
timer_started = False


frame_size = (int(watcher.get(3)), int(watcher.get(4)))
fourcc = cv2.VideoWriter_fourcc(*"mp4v")

while True:
    _, frame = watcher.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    faces = face_cascade.detectMultiScale(blur, 1.3, 5)
    bodies = face_cascade.detectMultiScale(blur, 1.3, 5)

    if len(faces) + len(bodies) > 0:
        if detection:
            timer_started = False
        else:
            detection = True
            msg()
            current_time = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
            out = cv2.VideoWriter(
                f"{current_time}.mp4", fourcc, 20, frame_size)
            print("Started Recording!")
    elif detection:
        if timer_started:
            if time.time() - detection_stopped_time >= 5:
                detection = False
                timer_started = False
                out.release()
                print('Stop Recording!')
        else:
            timer_started = True
            detection_stopped_time = time.time()

    if detection:
        out.write(frame)


    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) == ord('q'):
        break

out.release()
watcher.release()
cv2.destroyAllWindows()