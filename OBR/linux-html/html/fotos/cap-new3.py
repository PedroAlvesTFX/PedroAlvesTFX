from picamera2 import Picamera2
from PIL import Image, ImageDraw
import numpy as np
import time

# =====================================================
# CAMERA
# =====================================================

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

# =====================================================
# LOOP
# =====================================================

while True:

    frame = picam2.capture_array()

    #
    # Salva imagem original
    #
    frame_rgb = frame[:, :, ::-1]
#    frame_rgb = frame[:, :, ::]

    Image.fromarray(frame_rgb).save(
        "/bats/fotos/ramdisk/entrada.jpg",
        quality=90
    )

    #
    # Canais RGB
    #
    r = frame_rgb[:, :, 0].astype(np.float32)
    g = frame_rgb[:, :, 1].astype(np.float32)
    b = frame_rgb[:, :, 2].astype(np.float32)

    # =====================================================
    # DETECÇÃO PRETO
    # =====================================================

    ref_preto = 60

    preto = (
        (r < ref_preto) &
        (g < ref_preto) &
        (b < ref_preto)
    )

    # =====================================================
    # DETECÇÃO VERDE
    # =====================================================

    verde = (
        (g > r * 1.3) &
        (g > b * 1.3) &
        (g > 40)
    )

    # =====================================================
    # DETECÇÃO VERMELHO
    # =====================================================

    vermelho = (
        (r > g * 3.71) &
        (r > b * 3.71) &
        (r > 40)
    )

    # =====================================================
    # IMAGEM DE SAÍDA
    # =====================================================

    saida = np.full_like(frame, 255)

    #
    # Linha preta
    #
    saida[preto] = [0, 0, 0]

    #
    # Verde destacado
    #
    novo_g = np.minimum(g * 3, 255)

    saida[verde] = np.stack([
        np.zeros_like(r),
        novo_g,
        np.zeros_like(r)
    ], axis=-1)[verde]

    #
    # Vermelho destacado
    #
    novo_r = np.minimum(r * 3, 255)

    saida[vermelho] = np.stack([
        novo_r,
        np.zeros_like(g),
        np.zeros_like(b)
    ], axis=-1)[vermelho]

    # =====================================================
    # INTERSEÇÃO
    # =====================================================

    soma_colunas = np.sum(preto, axis=0)
    soma_linhas = np.sum(preto, axis=1)

    x_centro = np.argmax(soma_colunas)
    y_centro = np.argmax(soma_linhas)

    #
    # Cruz azul para debug
    #
    saida[:, x_centro] = [0, 0, 255]
    saida[y_centro, :] = [0, 0, 255]

    # =====================================================
    # FUNÇÃO QUADRANTE
    # =====================================================

    def quadrante(x, y):

        if x < x_centro and y < y_centro:
            return "SUP_ESQ"

        elif x > x_centro and y < y_centro:
            return "SUP_DIR"

        elif x < x_centro and y > y_centro:
            return "INF_ESQ"

        else:
            return "INF_DIR"

    status_verde = "SEM_VERDE"
    status_vermelho = "SEM_VERMELHO"

    # =====================================================
    # PROCESSA VERDE
    # =====================================================

    ys_v, xs_v = np.where(verde)

    if len(xs_v) > 30:

        min_x = np.min(xs_v)
        max_x = np.max(xs_v)

        min_y = np.min(ys_v)
        max_y = np.max(ys_v)

        largura = max_x - min_x
        altura = max_y - min_y

        area = largura * altura

        if area > 100:

            verde_x = int(np.mean(xs_v))
            verde_y = int(np.mean(ys_v))

            status_verde = (
                "VERDE:" +
                quadrante(
                    verde_x,
                    verde_y
                )
            )

            #
            # Centro verde
            #
            for dy in range(-5, 6):
                for dx in range(-5, 6):

                    xx = verde_x + dx
                    yy = verde_y + dy

                    if (
                        0 <= xx < 320 and
                        0 <= yy < 240
                    ):
                        saida[yy, xx] = [0,255,0]

    # =====================================================
    # PROCESSA VERMELHO
    # =====================================================

    ys_r, xs_r = np.where(vermelho)

    if len(xs_r) > 30:

        min_x = np.min(xs_r)
        max_x = np.max(xs_r)

        min_y = np.min(ys_r)
        max_y = np.max(ys_r)

        largura = max_x - min_x
        altura = max_y - min_y

        area = largura * altura

        if area > 100:

            vermelho_x = int(np.mean(xs_r))
            vermelho_y = int(np.mean(ys_r))

            status_vermelho = (
                "VERMELHO:" +
                quadrante(
                    vermelho_x,
                    vermelho_y
                )
            )

            #
            # Centro vermelho
            #
            for dy in range(-5, 6):
                for dx in range(-5, 6):

                    xx = vermelho_x + dx
                    yy = vermelho_y + dy

                    if (
                        0 <= xx < 320 and
                        0 <= yy < 240
                    ):
                        saida[yy, xx] = [255,0,0]

    # =====================================================
    # TEXTO
    # =====================================================

    mensagem = (
        f"{status_verde} | "
        f"{status_vermelho}"
    )

    print(mensagem)

    img_saida = Image.fromarray(
        saida.astype(np.uint8)
    )

    draw = ImageDraw.Draw(img_saida)

    draw.text(
        (10, 10),
        mensagem,
        fill=(0, 0, 255)
    )

    img_saida.save(
        "/bats/fotos/ramdisk/saida.jpg",
        quality=90
    )

    time.sleep(0.2)