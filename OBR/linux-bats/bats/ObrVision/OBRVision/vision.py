"""
Vision -- o "cerebro". Recebe um frame BGR, corrige iluminacao,
converte pra HSV, chama so os detectores relevantes pro estado atual
da missao, e guarda o resultado em self.objects (o que main.py manda
pro ESP32 via UART, e o que server.py expoe pra pagina web).

Correcao de iluminacao: white balance (gray world) + CLAHE no canal
de luminosidade (via LAB) -- ajuda bastante contra fita isolante
brilhante e variacao de luz entre locais de prova, mais barato que
alternativas mais sofisticadas.
"""

import copy
import threading
import time

import cv2
import numpy as np

from detectors.line import LineDetector
from detectors.red import RedDetector
from detectors.green import GreenDetector
from detectors.obstacle import ObstacleDetector


# Quais detectores rodam em cada estado da missao -- ajuste livre
# pra sua estrategia. Detectores fora da lista do estado atual nao
# sao processados (economiza CPU) e voltam um valor neutro/ausente,
# nao o ultimo valor conhecido de um estado anterior.
STATE_DETECTORS = {
    "INIT": [],
    "FOLLOW_LINE": ["line", "green", "red", "obstacle"],
    "GREEN": ["line", "green"],
    "RED": ["line", "red"],
    "OBSTACLE": ["obstacle", "line"],
    "RESCUE": ["green"],
    "FINISHED": [],
}

STATES = list(STATE_DETECTORS.keys())


class Vision:

    def __init__(self, config):
        self.config = config

        self.line_detector = LineDetector()
        self.red_detector = RedDetector()
        self.green_detector = GreenDetector()
        self.obstacle_detector = ObstacleDetector()

        self.state = "FOLLOW_LINE"

        self._objects_lock = threading.Lock()
        self.objects = self._empty_objects()

        self._frames_lock = threading.Lock()
        self._debug_frames = {}

        self._fps_last_t = time.monotonic()

    def set_state(self, state):
        if state not in STATE_DETECTORS:
            raise ValueError(f"Estado desconhecido: {state}. Validos: {STATES}")
        self.state = state

    def _empty_objects(self):
        return {
            "line": {"present": False, "error": 0.0, "angle": 0.0, "cx": None, "cy": None},
            "red": {"present": False, "distance_mm": None, "cx": None, "cy": None, "area": 0},
            "green": {"side": "none", "count": 0, "blobs": []},
            "obstacle": {"present": False, "cx": None, "area": 0},
            "fps": 0.0,
            "timing_ms": {},
            "state": self.state,
        }

    @staticmethod
    def _white_balance(bgr):
        # Gray world: assume que, na media, a cena e cinza -- reescala
        # cada canal pra empurrar a media geral pra essa direcao.
        # Barato e funciona bem o suficiente pra esse uso (nao
        # precisa de nada mais sofisticado tipo white-patch/retinex).
        result = bgr.astype(np.float32)
        b, g, r = cv2.split(result)

        mean_b, mean_g, mean_r = b.mean(), g.mean(), r.mean()
        mean_gray = (mean_b + mean_g + mean_r) / 3.0

        if mean_b > 1: b *= (mean_gray / mean_b)
        if mean_g > 1: g *= (mean_gray / mean_g)
        if mean_r > 1: r *= (mean_gray / mean_r)

        return np.clip(cv2.merge((b, g, r)), 0, 255).astype(np.uint8)

    @staticmethod
    def _clahe_luminosity(bgr):
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    def _correct_illumination(self, bgr):
        return self._clahe_luminosity(self._white_balance(bgr))

    def process(self, bgr):
        t_start = time.monotonic()
        cfg = self.config.get()

        corrected = self._correct_illumination(bgr)
        hsv = cv2.cvtColor(corrected, cv2.COLOR_BGR2HSV)

        h, w = bgr.shape[:2]
        blank_mask = np.zeros((h, w), dtype=np.uint8)

        active = STATE_DETECTORS.get(self.state, [])
        timing_ms = {}

        debug_frames = {
            "original": bgr,
            "hsv": cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR),
        }

        result = {}

        if "line" in active:
            t0 = time.monotonic()
            result["line"], debug_frames["black"] = self.line_detector.detect(corrected, hsv, cfg["line"])
            timing_ms["line"] = round((time.monotonic() - t0) * 1000, 2)
        else:
            result["line"] = self._empty_objects()["line"]
            debug_frames["black"] = blank_mask

        if "red" in active:
            t0 = time.monotonic()
            result["red"], debug_frames["red"] = self.red_detector.detect(corrected, hsv, cfg["red"])
            timing_ms["red"] = round((time.monotonic() - t0) * 1000, 2)
        else:
            result["red"] = self._empty_objects()["red"]
            debug_frames["red"] = blank_mask

        if "green" in active:
            t0 = time.monotonic()
            result["green"], debug_frames["green"] = self.green_detector.detect(corrected, hsv, cfg["green"])
            timing_ms["green"] = round((time.monotonic() - t0) * 1000, 2)
        else:
            result["green"] = self._empty_objects()["green"]
            debug_frames["green"] = blank_mask

        if "obstacle" in active:
            t0 = time.monotonic()
            result["obstacle"], _obstacle_mask = self.obstacle_detector.detect(corrected, hsv, cfg["obstacle"])
            timing_ms["obstacle"] = round((time.monotonic() - t0) * 1000, 2)
        else:
            result["obstacle"] = self._empty_objects()["obstacle"]

        now = time.monotonic()
        elapsed = now - self._fps_last_t
        self._fps_last_t = now
        fps = round(1.0 / elapsed, 1) if elapsed > 0 else 0.0

        objects = {
            "line": result["line"],
            "red": result["red"],
            "green": result["green"],
            "obstacle": result["obstacle"],
            "fps": fps,
            "timing_ms": timing_ms,
            "state": self.state,
            "total_ms": round((time.monotonic() - t_start) * 1000, 2),
        }

        with self._objects_lock:
            self.objects = objects

        with self._frames_lock:
            self._debug_frames = debug_frames

        return objects, debug_frames

    def get_objects(self):
        with self._objects_lock:
            return copy.deepcopy(self.objects)

    def get_debug_frame(self, name):
        """name: 'original' | 'black' | 'green' | 'red' | 'hsv'.
        Retorna None se ainda nao processou nenhum frame, ou se o
        nome nao existe."""
        with self._frames_lock:
            frame = self._debug_frames.get(name)
            return None if frame is None else frame.copy()
