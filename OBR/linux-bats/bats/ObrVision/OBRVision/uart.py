"""
UartSender -- unica coisa que fala com o ESP32. Nunca envia imagem,
so o JSON compacto com o que os detectores acharam. O ESP32 decide o
movimento -- esse modulo so entrega o dado, sem logica de controle.

Reconexao: se o cabo cair ou o ESP32 resetar, write() vai falhar --
em vez de derrubar o processo, tenta reabrir a porta periodicamente
(sem bloquear o loop principal por muito tempo a cada tentativa).
"""

import json
import time

import serial


class UartSender:

    def __init__(self, config):
        cfg = config.get_section("uart")
        self.port = cfg.get("port", "/dev/serial0")
        self.baud = cfg.get("baud", 115200)
        self.send_interval = 1.0 / max(1, cfg.get("send_hz", 20))

        self._serial = None
        self._last_send = 0.0
        self._last_reconnect_attempt = 0.0
        self._reconnect_interval = 2.0

        self._connect()

    def _connect(self):
        try:
            self._serial = serial.Serial(self.port, self.baud, timeout=0)
            print(f"[UART] Conectado em {self.port} @ {self.baud}")
        except serial.SerialException as e:
            self._serial = None
            print(f"[UART] Nao consegui abrir {self.port}: {e}")

    @staticmethod
    def _build_payload(objects):
        line = objects.get("line", {})
        red = objects.get("red", {})
        green = objects.get("green", {})
        obstacle = objects.get("obstacle", {})

        return {
            "linePresent": line.get("present", False),
            "lineError": line.get("error", 0.0),
            "lineAngle": line.get("angle", 0.0),
            "green": green.get("side", "none"),
            "redPresent": red.get("present", False),
            "redDistance": red.get("distance_mm"),
            "obstacle": obstacle.get("present", False),
            "state": objects.get("state", ""),
            "fps": objects.get("fps", 0.0),
        }

    def send(self, objects, force=False):
        """Respeita o send_hz configurado -- chame isso todo frame,
        ele mesmo decide se ja passou tempo suficiente pra mandar de
        novo (senao o ESP32 recebe muito mais dado do que precisa)."""
        now = time.monotonic()
        if not force and (now - self._last_send) < self.send_interval:
            return

        if self._serial is None:
            if now - self._last_reconnect_attempt >= self._reconnect_interval:
                self._last_reconnect_attempt = now
                self._connect()
            return

        payload = self._build_payload(objects)
        line = json.dumps(payload, separators=(",", ":")) + "\n"

        try:
            self._serial.write(line.encode("utf-8"))
            self._last_send = now
        except serial.SerialException as e:
            print(f"[UART] Erro ao escrever, vou tentar reconectar: {e}")
            self._serial.close()
            self._serial = None

    def close(self):
        if self._serial is not None:
            self._serial.close()
