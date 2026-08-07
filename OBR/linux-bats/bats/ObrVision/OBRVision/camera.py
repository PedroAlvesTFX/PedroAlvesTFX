"""
Camera -- unica responsabilidade: abrir a Picamera2, capturar frames
continuamente numa thread propria, e disponibilizar sempre o ULTIMO
frame pronto.

De proposito nao sabe nada sobre vermelho/verde/linha (isso e
trabalho do Vision) -- so entrega pixels. Isso significa: mesmo que
o processamento atrase, trave, ou o navegador da pagina web fique
pendurado, a captura continua rodando sem acumular atraso (sempre
processamos o frame mais recente disponivel, nunca uma fila
acumulada de frames antigos).

A rotacao de 180 graus e feita no proprio hardware/ISP da camera
(Transform do Picamera2), nao em software com cv2.rotate -- mais
barato de CPU.
"""

import threading
import time

from picamera2 import Picamera2
from libcamera import Transform


class Camera:

    def __init__(self, config):
        cam_cfg = config.get_section("camera")

        self.width = cam_cfg.get("width", 640)
        self.height = cam_cfg.get("height", 480)
        self.target_fps = cam_cfg.get("fps", 30)
        rotation = cam_cfg.get("rotation", 180)

        transform = Transform(hflip=(rotation == 180), vflip=(rotation == 180))

        self._picam2 = Picamera2()
        video_config = self._picam2.create_video_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"},
            transform=transform,
            buffer_count=4,
        )
        self._picam2.configure(video_config)

        self._lock = threading.Lock()
        self._frame = None
        self._frame_id = 0
        self._actual_fps = 0.0

        self._running = False
        self._thread = None

    def start(self):
        self._picam2.start()
        time.sleep(0.3)  # sensor precisa de um instante pra estabilizar exposicao

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._picam2.stop()

    def _capture_loop(self):
        frame_interval = 1.0 / self.target_fps
        last_fps_update = time.monotonic()
        frames_since_update = 0

        while self._running:
            t0 = time.monotonic()

            frame = self._picam2.capture_array()

            with self._lock:
                self._frame = frame
                self._frame_id += 1

            frames_since_update += 1
            now = time.monotonic()
            if now - last_fps_update >= 1.0:
                self._actual_fps = frames_since_update / (now - last_fps_update)
                frames_since_update = 0
                last_fps_update = now

            elapsed = time.monotonic() - t0
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_frame(self):
        """Retorna (frame, frame_id) -- frame_id serve pra quem
        chama saber se e um frame novo ou o mesmo de antes (ex.: pra
        nao reprocessar/reenviar o mesmo frame duas vezes)."""
        with self._lock:
            return self._frame, self._frame_id

    @property
    def fps(self):
        return self._actual_fps
