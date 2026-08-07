"""
LineDetector -- o mais importante do robo. O controle praticamente
so usa vision.line["error"] e vision.line["angle"].

Nao usa so HSV puro: preto "de verdade" tem V baixo E S baixo (fita
isolante brilhante pode ter V mais alto por causa de reflexo, mas
quase sempre mantem S baixo -- por isso o corte usa os dois canais).
"""

import cv2
import numpy as np


class LineDetector:

    def detect(self, bgr, hsv, cfg):
        h, w = bgr.shape[:2]

        y0 = int(h * cfg["roi_y_start"])
        roi_hsv = hsv[y0:h, :]

        mask_roi = cv2.inRange(
            roi_hsv,
            (0, 0, 0),
            (180, cfg["black_s_max"], cfg["black_v_max"]),
        )

        k = cfg.get("blur_ksize", 5)
        kernel = np.ones((k, k), np.uint8)
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_OPEN, kernel)
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_CLOSE, kernel)

        # mascara do tamanho do frame inteiro, so pra exibicao/debug
        # na pagina web -- facilita ver onde a ROI comeca.
        debug_mask = np.zeros((h, w), dtype=np.uint8)
        debug_mask[y0:h, :] = mask_roi

        contours, _ = cv2.findContours(mask_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {"present": False, "error": 0.0, "angle": 0.0, "cx": None, "cy": None}, debug_mask

        largest = max(contours, key=cv2.contourArea)

        if cv2.contourArea(largest) < cfg["min_area"]:
            return {"present": False, "error": 0.0, "angle": 0.0, "cx": None, "cy": None}, debug_mask

        moments = cv2.moments(largest)
        if moments["m00"] == 0:
            return {"present": False, "error": 0.0, "angle": 0.0, "cx": None, "cy": None}, debug_mask

        cx = moments["m10"] / moments["m00"]
        cy_roi = moments["m01"] / moments["m00"]
        cy = cy_roi + y0

        # fitLine da a direcao da linha (vx, vy) -- angulo relativo
        # ao "pra frente" (vertical da imagem). 0 = alinhado,
        # positivo = linha inclinada pra direita.
        vx, vy, _, _ = cv2.fitLine(largest, cv2.DIST_L2, 0, 0.01, 0.01).flatten()
        angle_deg = float(np.degrees(np.arctan2(vx, -vy)))

        error = (cx - w / 2.0) / (w / 2.0)  # normalizado: -1 (extrema esquerda) a +1 (extrema direita)

        return {
            "present": True,
            "error": round(float(error), 4),
            "angle": round(angle_deg, 2),
            "cx": round(float(cx), 1),
            "cy": round(float(cy), 1),
        }, debug_mask
