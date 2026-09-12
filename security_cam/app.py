from __future__ import annotations

import sys
import time

import cv2

from security_cam.alerts import Alerter
from security_cam.camera import Camera, CameraError
from security_cam.config import Settings
from security_cam.detector import DetectionResult, PersonDetector
from security_cam.recorder import ClipRecorder, PreRollBuffer


def annotate(frame, detection: DetectionResult, recording: bool):
    if detection.found:
        cv2.putText(
            frame,
            f"PERSON {detection.confidence:.2f}",
            (16, 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
    if recording:
        cv2.circle(frame, (frame.shape[1] - 28, 28), 10, (0, 0, 255), -1)
        cv2.putText(
            frame,
            "REC",
            (frame.shape[1] - 86, 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )
    return frame


def run(settings: Settings) -> None:
    try:
        camera = Camera(settings.camera_index)
    except CameraError as exc:
        sys.exit(str(exc))

    fps = camera.fps(settings.fps_fallback)
    buffer = PreRollBuffer(settings.preroll_seconds, fps)
    recorder = ClipRecorder(settings.output_dir, camera.frame_size, fps)
    alerter = Alerter(settings)
    detector = PersonDetector(settings.confidence, settings.model_path)

    detection = False
    detection_stopped_time = None
    timer_started = False

    print(
        f"Security CAM v2 — MediaPipe Pose, preroll {settings.preroll_seconds:.1f}s, "
        f"{'local-only' if settings.local_only else 'WhatsApp alerts'}. Press q to quit."
    )

    try:
        while True:
            try:
                frame = camera.read()
            except CameraError as exc:
                print(exc)
                break

            buffer.append(frame)
            result = detector.detect(frame)
            just_started = False

            if result.found:
                if detection:
                    timer_started = False
                else:
                    detection = True
                    alerter.send()
                    recorder.start(buffer.snapshot())
                    just_started = True
                    print("Started Recording!")
            elif detection:
                if timer_started:
                    if time.time() - detection_stopped_time >= settings.stop_delay_seconds:
                        detection = False
                        timer_started = False
                        recorder.stop()
                        print("Stop Recording!")
                else:
                    timer_started = True
                    detection_stopped_time = time.time()

            # start() already flushed the buffer, including this frame.
            if recorder.is_recording and not just_started:
                recorder.write(frame)

            if settings.preview:
                annotate(frame, result, recorder.is_recording)
                cv2.imshow("Camera", frame)
                if cv2.waitKey(1) == ord("q"):
                    break
    except KeyboardInterrupt:
        print("Interrupted.")
    finally:
        recorder.stop()
        detector.close()
        camera.release()
        if settings.preview:
            cv2.destroyAllWindows()
