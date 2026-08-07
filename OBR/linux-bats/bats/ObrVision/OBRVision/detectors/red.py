"""
RedDetector -- so importa quando estamos PRATICAMENTE em cima do
vermelho (ROI proxima do robo, nao "la na frente"). Converte a
posicao Y do centro do vermelho em distancia real (mm) usando uma
regressao linear simples a partir de pontos de calibracao manual
(ver config["red"]["calib_points"]).

Vermelho estoura pelos dois lados do circulo de matiz (H=0 e H=180
no OpenCV) -- por isso duas faixas HSV, unidas com bitwise_or.
"""

import cv2
import numpy as np


class RedDetector:

    def __init__(self):
        self._calib_a = 0.0
        self._calib_b = 0.0
        self._calib_key = None  # evita recalcular regressao todo frame a toa

    def _ensure_calibration(self, calib_points):
        key = tuple(tuple(p) for p in calib_points)
        if key == self._calib_key:
            return
        self._calib_key = key

        ys = np.array([p[0] for p in calib_points], dtype=float)
        mms = np.array([p[1] for p in calib_points], dtype=float)

        # y -> mm: ajuste linear (regressao) a partir dos pontos
        # medidos manualmente com a camera fixa. Recalibrar =
        # remedir 2-3 pontos e atualizar calib_points no config.
        self._calib_a, self._calib_b = np.polyfit(ys, mms, 1)

    def _distance_mm(self, y):
        return float(self._calib_a * y + self._calib_b)

    def detect(self, bgr, hsv, cfg):
        self._ensure_calibration(cfg["calib_points"])

        h, w = bgr.shape[:2]
        y0 = int(h * cfg["roi_y_start"])
        roi_hsv = hsv[y0:h, :]

        mask1 = cv2.inRange(
            roi_hsv,
            (cfg["h1_min"], cfg["s_min"], cfg["v_min"]),
            (cfg["h1_max"], 255, 255),
        )
        mask2 = cv2.inRange(
            roi_hsv,
            (cfg["h2_min"], cfg["s_min"], cfg["v_min"]),
            (cfg["h2_max"], 255, 255),
        )
        mask_roi = cv2.bitwise_or(mask1, mask2)

        kernel = np.ones((5, 5), np.uint8)
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_OPEN, kernel)

        debug_mask = np.zeros((h, w), dtype=np.uint8)
        debug_mask[y0:h, :] = mask_roi

        contours, _ = cv2.findContours(mask_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {"present": False, "distance_mm": None, "cx": None, "cy": None, "area": 0}, debug_mask

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        if area < cfg["min_area"]:
            return {"present": False, "distance_mm": None, "cx": None, "cy": None, "area": 0}, debug_mask

        moments = cv2.moments(largest)
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"] + y0

        return {
            "present": True,
            "distance_mm": round(self._distance_mm(cy), 1),
            "cx": round(float(cx), 1),
            "cy": round(float(cy), 1),
            "area": int(area),
        }, debug_mask
