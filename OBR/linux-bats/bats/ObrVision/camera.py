from picamera2 import Picamera2
import threading
import cv2
import time

from config import *

class Camera:

    def __init__(self):

        self.picam = Picamera2()

        cfg = self.picam.create_video_configuration(

            main={
                "size": (WIDTH, HEIGHT),
                "format": "RGB888"
            },

            controls={

                "FrameDurationLimits": (
                    int(1e6/FPS),
                    int(1e6/FPS)
                ),

                "AeEnable": True,
                "AwbEnable": True

            }

        )

        self.picam.configure(cfg)

        self.picam.start()

        time.sleep(1)

        self.frame = None

        self.running = True

        self.lock = threading.Lock()

        self.thread = threading.Thread(
            target=self.update,
            daemon=True
        )

        self.thread.start()

    def update(self):

        while self.running:

            img = self.picam.capture_array()

            img = cv2.rotate(
                img,
                cv2.ROTATE_180
            )

            with self.lock:

                self.frame = img

    def read(self):

        with self.lock:

            if self.frame is None:
                return None

            return self.frame.copy()

    def stop(self):

        self.running = False

        self.thread.join()

        self.picam.stop()