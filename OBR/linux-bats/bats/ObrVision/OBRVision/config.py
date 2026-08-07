"""
Config -- unica fonte de verdade pros parametros calibraveis
(thresholds HSV, ROIs, porta serial, etc). Ve config/hsv.json.

Thread-safe de proposito: o Vision (thread de processamento) LE a
config a cada frame, e o Server (Flask, thread separada) ESCREVE
quando alguem mexe nos sliders da pagina web -- sem lock, dava pra
ler um dicionario pela metade atualizado.

Nunca recompila nada: os detectores leem `config.get()` a cada frame,
entao uma mudanca no slider ja vale no proximo frame processado.
"""

import json
import threading
import copy
import os

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "config", "hsv.json")


class Config:

    def __init__(self, path=DEFAULT_PATH):
        self._path = path
        self._lock = threading.Lock()
        self._data = {}
        self.load()

    def load(self):
        with self._lock:
            if os.path.exists(self._path):
                with open(self._path, "r") as f:
                    self._data = json.load(f)
            else:
                raise FileNotFoundError(
                    f"Config nao encontrada em {self._path} -- "
                    f"o repositorio ja vem com um config/hsv.json default, "
                    f"confira se ele nao foi apagado."
                )

    def save(self):
        with self._lock:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w") as f:
                json.dump(self._data, f, indent=4)

    def get(self):
        """Copia profunda -- quem chama pode mexer a vontade sem
        afetar o estado real (so update() muda de verdade)."""
        with self._lock:
            return copy.deepcopy(self._data)

    def get_section(self, section):
        with self._lock:
            return copy.deepcopy(self._data.get(section, {}))

    def update(self, partial):
        """Merge raso por secao -- partial = {"red": {"h1_max": 10}}
        atualiza so red.h1_max, mantem o resto de "red" intocado."""
        with self._lock:
            for section, values in partial.items():
                if section not in self._data:
                    self._data[section] = {}
                self._data[section].update(values)

    def update_and_save(self, partial):
        self.update(partial)
        self.save()
