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

    verde = ( (g > r * 1.1) & (g > b * 1.1) & (g > 30) &  (r < 200) )
    saida = np.full_like(frame, 255)

    ref_preto=70
    preto = ( (r < ref_preto) &    (g < ref_preto) &    (b < ref_preto) ) 
    saida[preto] = [0, 0, 0]

    for y in range(frame.shape[0]):
        linha = verde[y]
        contador = 0

        for x in range(frame.shape[1]):

            if linha[x]:
                contador += 1
            else:
                contador = 0

            if contador > 10:
                novo_g = min( int(frame[y, x, 1]) * 3, 255)

                saida[y, x] = [  frame[y, x, 0],   novo_g,    frame[y, x, 2]   ]

    Image.fromarray(saida).save( "/bats/fotos/ramdisk/saida.jpg")
    print("Imagem processada")
    time.sleep(0.2)