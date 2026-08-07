from picamera2 import Picamera2
from time import sleep
import numpy as np
import time

# ==========================================
# CAMERA
# ==========================================

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={
        "size": (64, 48),
        "format": "RGB888"
    }
)

picam2.configure(config)

picam2.start()

sleep(2)

# ==========================================
# CAPTURA
# ==========================================

t0 = time.perf_counter()

img = picam2.capture_array()

t1 = time.perf_counter()

# ==========================================
# INFO DO FRAME
# ==========================================

print()
print("Frame:", img.shape)
print("Tipo :", img.dtype)

# ==========================================
# REMOVE CANAL EXTRA (SE EXISTIR)
# ==========================================

t2 = time.perf_counter()

if len(img.shape) == 3 and img.shape[2] > 3:
    img = img[:, :, :3]

t3 = time.perf_counter()

# ==========================================
# DOWNSAMPLE
# pega 1 pixel a cada 2
# ==========================================

img = img[::2, ::2]

t4 = time.perf_counter()

# ==========================================
# SPLIT RGB
# ==========================================

R = img[:, :, 0].astype(np.int16)
G = img[:, :, 1].astype(np.int16)
B = img[:, :, 2].astype(np.int16)

t5 = time.perf_counter()

# ==========================================
# CLASSIFICAÇÃO
# ==========================================

verde = (
    (G > 80) &
    (G > R + 25) &
    (G > B + 25)
)

branco = (
    (R > 170) &
    (G > 170) &
    (B > 170)
)

preto = (
    (R < 50) &
    (G < 50) &
    (B < 50)
)

t6 = time.perf_counter()

# ==========================================
# CRIA MAPA
# ==========================================

mapa = np.zeros(
    (img.shape[0], img.shape[1]),
    dtype=np.uint8
)

mapa[verde] = 1
mapa[branco] = 2
mapa[preto] = 3

t7 = time.perf_counter()

# ==========================================
# PRINT
# ==========================================

cores = {
    0: '\033[91m',
    1: '\033[92m',
    2: '\033[97m',
    3: '\033[90m'
}

chars = {
    0: 'X',
    1: 'G',
    2: 'W',
    3: 'P'
}

tp0 = time.perf_counter()

for linha in mapa:

    texto = ""

    for v in linha:

        texto += (
            cores[int(v)] +
            chars[int(v)] +
            '\033[0m'
        )

    print(texto)

tp1 = time.perf_counter()

# ==========================================
# TEMPOS
# ==========================================

print()
print("============== TEMPOS ==============")
print(f"capture_array      : {(t1-t0)*1000:.2f} ms")
print(f"remove_canal_extra : {(t3-t2)*1000:.2f} ms")
print(f"downsample         : {(t4-t3)*1000:.2f} ms")
print(f"split_rgb          : {(t5-t4)*1000:.2f} ms")
print(f"classificacao      : {(t6-t5)*1000:.2f} ms")
print(f"criar_mapa         : {(t7-t6)*1000:.2f} ms")
print(f"impressao          : {(tp1-tp0)*1000:.2f} ms")

print()
print(
    f"TOTAL              : "
    f"{(tp1-t0)*1000:.2f} ms"
)
print("====================================")