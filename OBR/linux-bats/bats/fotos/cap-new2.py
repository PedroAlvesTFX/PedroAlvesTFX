from picamera2 import Picamera2
from PIL import Image
import numpy as np
import time

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (320, 240), "format": "RGB888"}
)

picam2.configure(config)

picam2.set_controls({
    "AeEnable": False,
    "AwbEnable": False,
    "ExposureTime": 50000,
    "AnalogueGain": 2.0
})

picam2.start()

while True:

    frame = picam2.capture_array()

    frame_rgb = frame[:, :, ::-1]

    Image.fromarray(frame_rgb).save(
        "/bats/fotos/ramdisk/entrada.jpg",
        quality=90
    )

    r = frame[:, :, 0].astype(np.float32)
    g = frame[:, :, 1].astype(np.float32)
    b = frame[:, :, 2].astype(np.float32)

    #
    # Detecta preto
    #
    ref_preto = 70

    preto = (
        (r < ref_preto) &
        (g < ref_preto) &
        (b < ref_preto)
    )

    #
    # Detecta verde
    #
    verde = (
        (g > r * 1.3) &
        (g > b * 1.3) &
        (g > 40)
    )

    #
    # Imagem de saída
    #
    saida = np.full_like(frame, 255)

    saida[preto] = [0,0,0]

    #
    # Procura centro da cruz
    #
    soma_colunas = np.sum(preto, axis=0)
    soma_linhas  = np.sum(preto, axis=1)

    x_centro = np.argmax(soma_colunas)
    y_centro = np.argmax(soma_linhas)

    #
    # Desenha a cruz detectada
    #
    saida[:, x_centro] = [255,0,0]
    saida[y_centro, :] = [255,0,0]

    #
    # Procura centro do bloco verde
    #
    ys, xs = np.where(verde)

    if len(xs) > 20:

        verde_x = int(np.mean(xs))
        verde_y = int(np.mean(ys))

        #
        # Marca centro do verde
        #
        for dy in range(-4,5):
            for dx in range(-4,5):

                yy = verde_y + dy
                xx = verde_x + dx

                if (
                    0 <= yy < frame.shape[0]
                    and
                    0 <= xx < frame.shape[1]
                ):
                    saida[yy,xx] = [0,0,255]

        #
        # Determina quadrante
        #
        if verde_x < x_centro and verde_y < y_centro:
            quadrante = "SUPERIOR ESQUERDO"

        elif verde_x > x_centro and verde_y < y_centro:
            quadrante = "SUPERIOR DIREITO"

        elif verde_x < x_centro and verde_y > y_centro:
            quadrante = "INFERIOR ESQUERDO"

        else:
            quadrante = "INFERIOR DIREITO"

        print(
            f"Cruz=({x_centro},{y_centro}) "
            f"Verde=({verde_x},{verde_y}) "
            f"{quadrante}"
        )

    else:
        print("Quadrado verde nao encontrado")

    Image.fromarray(saida).save(
        "/bats/fotos/ramdisk/saida.jpg",
        quality=90
    )

    time.sleep(0.2)