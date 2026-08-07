import cv2
import numpy as np
from picamera2 import Picamera2
from time import sleep

# ==========================
# TIRA FOTO
# ==========================

picam2 = Picamera2()

config = picam2.create_still_configuration(
    main={"size": (160, 120)}
)

picam2.configure(config)

picam2.start()

sleep(2)

picam2.capture_file("foto.jpg")

picam2.stop()

print("Foto salva!")

# ==========================
# ABRE FOTO
# ==========================

img = cv2.imread("foto.jpg")

if img is None:
    print("Erro ao abrir imagem")
    exit()

# ==========================
# CONVERTE PARA HSV
# ==========================

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# ==========================
# VERDE
# ==========================

verde_min = np.array([35, 50, 50])
verde_max = np.array([85, 255, 255])

mask_verde = cv2.inRange(hsv, verde_min, verde_max)

# ==========================
# BRANCO
# ==========================

branco_min = np.array([0, 0, 180])
branco_max = np.array([180, 50, 255])

mask_branco = cv2.inRange(hsv, branco_min, branco_max)

# ==========================
# PRETO
# ==========================

preto_min = np.array([0, 0, 0])
preto_max = np.array([180, 255, 50])

mask_preto = cv2.inRange(hsv, preto_min, preto_max)

# ==========================
# CONTAGEM
# ==========================

verde = cv2.countNonZero(mask_verde)
branco = cv2.countNonZero(mask_branco)
preto = cv2.countNonZero(mask_preto)

print()
print("Pixels verdes :", verde)
print("Pixels brancos:", branco)
print("Pixels pretos :", preto)

# ==========================
# QUAL COR DOMINA?
# ==========================

maior = max(verde, branco, preto)

if maior == verde:
    print("COR PREDOMINANTE: VERDE")

elif maior == branco:
    print("COR PREDOMINANTE: BRANCO")

else:
    print("COR PREDOMINANTE: PRETO")