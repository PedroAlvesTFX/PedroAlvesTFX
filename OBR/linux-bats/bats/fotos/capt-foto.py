from picamera2 import Picamera2
import cv2
import time

picam2 = Picamera2()

picam2.set_controls({
    "AeEnable": False,
    "AwbEnable": False,
    "ExposureTime": 10000,
    "AnalogueGain": 2.0
})

config = picam2.create_preview_configuration(
    main={"size": (320,240), "format":"RGB888"}
)

picam2.configure(config)
picam2.start()

while True:

    frame = picam2.capture_array()

    # Processa aqui
    cv2.imwrite("/bats/fotos/ramdisk/entrada.jpg", frame)

    print(frame.shape)

    time.sleep(0.5)