"""
Server -- pagina web de calibracao/monitoramento (Flask). So LE o
que Vision/Config ja tem pronto -- nao processa imagem nenhuma aqui,
so serve o que a thread de visao ja calculou (por isso a pagina
travar/o navegador fechar nunca afeta o robo, ver comentario em
camera.py).

Roda numa thread separada da captura/processamento (ver main.py) --
sao mundos desacoplados de proposito.
"""

import time

import cv2
from flask import Flask, Response, jsonify, render_template, request

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


def create_app(config, vision, uart, camera):
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/video_feed/<name>")
    def video_feed(name):
        if name not in ("original", "black", "green", "red", "hsv"):
            return "Stream desconhecido -- use original/black/green/red/hsv", 404

        def generate():
            # ~15 FPS de stream -- nao precisa acompanhar a taxa
            # cheia do pipeline, e economiza CPU/banda pro navegador.
            interval = 1.0 / 15
            while True:
                frame = vision.get_debug_frame(name)
                if frame is not None:
                    if frame.ndim == 2:  # mascara em escala de cinza
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ok:
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
                        )
                time.sleep(interval)

        return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.route("/api/status")
    def api_status():
        objects = vision.get_objects()

        cpu_percent = psutil.cpu_percent(interval=None) if _HAS_PSUTIL else None

        return jsonify({
            "objects": objects,
            "camera_fps": round(camera.fps, 1),
            "cpu_percent": cpu_percent,
            "uart_connected": uart._serial is not None,
            "state": vision.state,
        })

    @app.route("/api/config", methods=["GET"])
    def api_config_get():
        return jsonify(config.get())

    @app.route("/api/config", methods=["POST"])
    def api_config_update():
        # Aplica na hora (o proximo frame ja usa), NAO salva em
        # disco ainda -- so o botao "Salvar" persiste. Assim da pra
        # testar um slider sem sujar o config/hsv.json se nao gostar.
        partial = request.get_json(force=True)
        config.update(partial)
        return jsonify({"ok": True})

    @app.route("/api/config/save", methods=["POST"])
    def api_config_save():
        config.save()
        return jsonify({"ok": True})

    @app.route("/api/config/load", methods=["POST"])
    def api_config_load():
        config.load()
        return jsonify({"ok": True, "config": config.get()})

    @app.route("/api/state", methods=["POST"])
    def api_state():
        body = request.get_json(force=True)
        try:
            vision.set_state(body["state"])
        except (KeyError, ValueError) as e:
            return jsonify({"ok": False, "error": str(e)}), 400
        return jsonify({"ok": True, "state": vision.state})

    return app
