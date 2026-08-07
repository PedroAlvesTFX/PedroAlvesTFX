import cv2
import numpy as np
import time
from flask import Flask, Response

# ==========================================================
# CONFIG
# ==========================================================

WIDTH = 640
HEIGHT = 480
FPS = 30

SHOW_RED = True
SHOW_GREEN = True
SHOW_BLACK = True

# ==========================================================
# CAMERA
# ==========================================================

camera = cv2.VideoCapture(0)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
camera.set(cv2.CAP_PROP_FPS, FPS)

kernel = np.ones((5, 5), np.uint8)

# ==========================================================
# FLASK
# ==========================================================

app = Flask(__name__)

# ==========================================================
# FPS
# ==========================================================

last_time = time.time()
fps = 0

# ==========================================================
# DRAW DETECTIONS
# ==========================================================

def draw_objects(frame, mask, color, text):

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for contour in contours:

        area = cv2.contourArea(contour)

        if area < 300:
            continue

        x, y, w, h = cv2.boundingRect(contour)

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            color,
            2
        )

        cv2.putText(
            frame,
            text,
            (x, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

# ==========================================================
# STREAM
# ==========================================================

def generate():

    global fps
    global last_time

    while True:

        ok, frame = camera.read()

        if not ok:
            continue

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # ===========================
        # RED
        # ===========================

        if SHOW_RED:

            lower1 = np.array([0,120,70])
            upper1 = np.array([10,255,255])

            lower2 = np.array([170,120,70])
            upper2 = np.array([180,255,255])

            red = cv2.inRange(hsv, lower1, upper1)
            red |= cv2.inRange(hsv, lower2, upper2)

            red = cv2.morphologyEx(red, cv2.MORPH_OPEN, kernel)
            red = cv2.morphologyEx(red, cv2.MORPH_CLOSE, kernel)

            draw_objects(frame, red, (0,0,255), "RED")

        # ===========================
        # GREEN
        # ===========================

        if SHOW_GREEN:

            lower = np.array([35,60,60])
            upper = np.array([90,255,255])

            green = cv2.inRange(hsv, lower, upper)

            green = cv2.morphologyEx(green, cv2.MORPH_OPEN, kernel)
            green = cv2.morphologyEx(green, cv2.MORPH_CLOSE, kernel)

            draw_objects(frame, green, (0,255,0), "GREEN")

        # ===========================
        # BLACK
        # ===========================

        if SHOW_BLACK:

            lower = np.array([0,0,0])
            upper = np.array([180,255,60])

            black = cv2.inRange(hsv, lower, upper)

            black = cv2.morphologyEx(black, cv2.MORPH_OPEN, kernel)
            black = cv2.morphologyEx(black, cv2.MORPH_CLOSE, kernel)

            draw_objects(frame, black, (60,60,60), "BLACK")

        # ===========================
        # FPS
        # ===========================

        now = time.time()

        fps = 1.0 / (now - last_time)

        last_time = now

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10,30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255,0,0),
            2
        )

        _, jpg = cv2.imencode(".jpg", frame)

        frame_bytes = jpg.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame_bytes +
            b'\r\n'
        )

# ==========================================================
# WEB
# ==========================================================

@app.route("/")
def index():

    return """
    <html>

    <head>

    <title>OBR Vision</title>

    <style>

    body{

        background:#111;
        text-align:center;
        color:white;
        font-family:Arial;

    }

    img{

        width:90%;
        max-width:900px;
        border:4px solid white;

    }

    </style>

    </head>

    <body>

        <h1>OBR Vision</h1>

        <img src="/video">

    </body>

    </html>
    """

@app.route("/video")
def video():

    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# ==========================================================

if __name__ == "__main__":

    print("Camera server started")

    app.run(
        host="0.0.0.0",
        port=8080,
        threaded=True
    )