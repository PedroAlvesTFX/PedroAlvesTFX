"""
ObstacleDetector -- detecta um blob ESCURO grande numa faixa do
meio da imagem (nem tao perto quanto a ROI do vermelho, nem a ROI
inferior da linha), excluindo uma faixa vertical central estreita
(onde a propria linha preta passa) pra nao confundir "seguindo a
linha normalmente" com "tem obstaculo".

Esse e o detector que mais depende do layout exato da prova (o
documento original nao detalhou o algoritmo, so a necessidade) --
os parametros em config["obstacle"] (area minima, ROI, margem de
exclusao) sao ponto de partida, espere precisar recalibrar em cima
da pista/obstaculos reais da categoria.
"""

import cv2
import numpy as np


class ObstacleDetector:

    def detect(self, bgr, hsv, cfg):
        h, w = bgr.shape[:2]

        y0 = int(h * cfg["roi_y_start"])
        y1 = int(h * cfg["roi_y_end"])
        roi_hsv = hsv[y0:y1, :]

        mask_roi = cv2.inRange(
            roi_hsv,
            (0, 0, 0),
            (180, cfg["s_max"], cfg["v_max"]),
        )

        # exclui a faixa central estreita (onde a linha normalmente
        # esta) -- so queremos pegar blobs escuros LARGOS (obstaculo
        # de verdade), nao a linha fina que estamos seguindo.
        margin = cfg.get("line_exclusion_margin_px", 30)
        cx_frame = w // 2
        mask_roi[:, max(0, cx_frame - margin):min(w, cx_frame + margin)] = 0

        kernel = np.ones((5, 5), np.uint8)
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_OPEN, kernel)
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_CLOSE, kernel)

        debug_mask = np.zeros((h, w), dtype=np.uint8)
        debug_mask[y0:y1, :] = mask_roi

        contours, _ = cv2.findContours(mask_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {"present": False, "cx": None, "area": 0}, debug_mask

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        if area < cfg["min_area"]:
            return {"present": False, "cx": None, "area": 0}, debug_mask

        moments = cv2.moments(largest)
        cx = moments["m10"] / moments["m00"] if moments["m00"] else None

        return {
            "present": True,
            "cx": round(float(cx), 1) if cx is not None else None,
            "area": int(area),
        }, debug_mask
