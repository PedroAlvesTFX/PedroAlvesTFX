import spidev
import RPi.GPIO as GPIO
import time

NSS = 6
RST = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(NSS, GPIO.OUT)
GPIO.setup(RST, GPIO.OUT)
GPIO.output(NSS, 1)
GPIO.output(RST, 0)
time.sleep(0.2)
GPIO.output(RST, 1)
time.sleep(0.1)
GPIO.output(RST, 0)

spi = spidev.SpiDev()
spi.open(0, 0)  # CE0 não importa, CS será manual
spi.max_speed_hz = 500000
spi.mode = 0

def read_reg(addr):
    GPIO.output(NSS, 0)
    time.sleep(0.1)
    resp = spi.xfer2([addr & 0x7F, 0x00])
    GPIO.output(NSS, 1)
    return resp[1]

version = read_reg(0x42)
print("Versão SX127x:", hex(version))
