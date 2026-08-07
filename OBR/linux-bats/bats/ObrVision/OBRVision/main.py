"""
main.py -- ponto de entrada. Sobe Config, Camera, Vision, UartSender
e o servidor web. O loop captura->processa->manda-UART roda numa
thread separada da pagina Flask -- de proposito (ver comentario em
camera.py): a pagina nunca pode atrasar o robo.
"""

import threading
import time

from config import Config
from camera import Camera
from vision import Vision
from uart import UartSender
from server import create_app


def vision_loop(camera, vision, uart, stop_event):
    last_frame_id = -1

    while not stop_event.is_set():
        frame, frame_id = camera.get_frame()

        if frame is None or frame_id == last_frame_id:
            time.sleep(0.005)
            continue

        last_frame_id = frame_id

        objects, _debug_frames = vision.process(frame)
        uart.send(objects)


def main():
    config = Config()

    camera = Camera(config)
    camera.start()

    vision = Vision(config)
    uart = UartSender(config)

    stop_event = threading.Event()
    thread = threading.Thread(
        target=vision_loop,
        args=(camera, vision, uart, stop_event),
        daemon=True,
    )
    thread.start()

    app = create_app(config, vision, uart, camera)
    server_cfg = config.get_section("server")

    try:
        app.run(
            host=server_cfg.get("host", "0.0.0.0"),
            port=server_cfg.get("port", 8000),
            threaded=True,
        )
    finally:
        stop_event.set()
        thread.join(timeout=2.0)
        camera.stop()
        uart.close()


if __name__ == "__main__":
    main()
