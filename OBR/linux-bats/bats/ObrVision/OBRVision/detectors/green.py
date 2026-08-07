"""
GreenDetector -- procura em praticamente toda a imagem (nao so uma
ROI pequena, diferente de linha/vermelho). Classifica em none / left
/ right / both, dependendo de onde os blobs verdes aparecem em
relacao ao centro da imagem.

merge_gap_px: blobs verdes proximos (a mesma marcacao pode fragmentar
em 2-3 contornos por causa de reflexo/sombra) sao unidos ANTES de
contar lados -- um dilate com esse raio faz esse trabalho sem
precisar de logica de agrupamento manual.
"""

import cv2
import numpy as np


class GreenDetector:

    def detect(self, bgr, hsv, cfg):
        h, w = bgr.shape[:2]

        mask = cv2.inRange(
            hsv,
            (cfg["h_min"], cfg["s_min"], cfg["v_min"]),
            (cfg["h_max"], 255, 255),
        )

        gap = max(1, cfg.get("merge_gap_px", 40))
        kernel = np.ones((gap, gap), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        centers = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < cfg["min_area"]:
                continue
            m = cv2.moments(c)
            if m["m00"] == 0:
                continue
            cx = m["m10"] / m["m00"]
            cy = m["m01"] / m["m00"]
            centers.append((cx, cy, area))

        if not centers:
            return {"side": "none", "count": 0, "blobs": []}, mask

        center_x = w / 2.0
        has_left = any(c[0] < center_x for c in centers)
        has_right = any(c[0] >= center_x for c in centers)

        if has_left and has_right:
            side = "both"
        elif has_left:
            side = "left"
        else:
            side = "right"

        blobs = [{"cx": round(c[0], 1), "cy": round(c[1], 1), "area": int(c[2])} for c in centers]

        return {"side": side, "count": len(centers), "blobs": blobs}, mask
