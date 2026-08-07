import spidev
import RPi.GPIO as GPIO
import time
import json
import base64
import signal
import sys

# ================= CONFIG =================
FREQ = 912300000
SF = 10
BW = 125  # 125, 250 ou 500

PIN_NSS = 6
PIN_DIO0 = 5
PIN_RST = 3
#    "pin_nss": 6,
#    "pin_dio0": 7,
#    "pin_rst": 3,
SPI_BUS = 0
SPI_DEV = 0
# ==========================================

# REGISTERS
REG_FIFO = 0x00
REG_OPMODE = 0x01
REG_FRF_MSB = 0x06
REG_FRF_MID = 0x07
REG_FRF_LSB = 0x08
REG_LNA = 0x0C
REG_FIFO_ADDR_PTR = 0x0D
REG_FIFO_RX_BASE_AD = 0x0F
REG_FIFO_RX_CURRENT_ADDR = 0x10
REG_IRQ_FLAGS = 0x12
REG_RX_NB_BYTES = 0x13
REG_PKT_SNR_VALUE = 0x19
REG_PKT_RSSI_VALUE = 0x1A
REG_MODEM_CONFIG = 0x1D
REG_MODEM_CONFIG2 = 0x1E
REG_SYMB_TIMEOUT_LSB = 0x1F
REG_MODEM_CONFIG3 = 0x26
REG_SYNC_WORD = 0x39
REG_VERSION = 0x42
REG_PAYLOAD_LENGTH = 0x22
REG_MAX_PAYLOAD_LENGTH = 0x23
REG_HOP_PERIOD = 0x24

MODE_SLEEP = 0x80
MODE_STDBY = 0x81
MODE_RX_CONT = 0x85

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEV)
spi.max_speed_hz = 5000000
spi.mode = 0


GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_RST, GPIO.OUT)
GPIO.setup(PIN_DIO0, GPIO.IN) #nao era pra dar erro mas dá.....
GPIO.setup(PIN_NSS, GPIO.OUT)

def cleanup(sig=None, frame=None):
    print("\nEncerrando...")
    GPIO.cleanup()
    spi.close()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)

def write_reg(addr, val):
    spi.xfer2([addr | 0x80, val])

def read_reg(addr):
    return spi.xfer2([addr & 0x7F, 0x00])[1]

def reset_lora():
    GPIO.output(PIN_RST, 1)
    time.sleep(0.1)
    GPIO.output(PIN_RST, 0)
    time.sleep(0.1)

    GPIO.output(PIN_NSS, 0)
    time.sleep(0.1)


def set_freq(freq):
    frf = int((freq << 19) / 32000000)
    write_reg(REG_FRF_MSB, (frf >> 16) & 0xFF)
    write_reg(REG_FRF_MID, (frf >> 8) & 0xFF)
    write_reg(REG_FRF_LSB, frf & 0xFF)

def setup_lora():
    version = read_reg(REG_VERSION)
    if version != 0x12:
        print(f"Chip não detectado! Versão: {hex(version)}")
        sys.exit(1)

    print("SX1276 detectado!")

    write_reg(REG_OPMODE, MODE_SLEEP)
    time.sleep(0.1)

    set_freq(FREQ)
    write_reg(REG_SYNC_WORD, 0x34)

    # BW
    bw_bits = {125: 0x70, 250: 0x80, 500: 0x90}.get(BW, 0x70)
    cr_bits = 0x02  # 4/5
    write_reg(REG_MODEM_CONFIG, bw_bits | cr_bits)

    write_reg(REG_MODEM_CONFIG2, (SF << 4) | 0x04)

    if SF >= 11:
        write_reg(REG_MODEM_CONFIG3, 0x0C)
    else:
        write_reg(REG_MODEM_CONFIG3, 0x04)

    write_reg(REG_SYMB_TIMEOUT_LSB, 0x08)
    write_reg(REG_MAX_PAYLOAD_LENGTH, 0x80)
    write_reg(REG_PAYLOAD_LENGTH, 0x40)
    write_reg(REG_HOP_PERIOD, 0xFF)
    write_reg(REG_FIFO_ADDR_PTR, read_reg(REG_FIFO_RX_BASE_AD))
    write_reg(REG_LNA, 0x23)

    write_reg(REG_OPMODE, MODE_RX_CONT)
    print(f"Escutando: SF{SF} BW{BW} {FREQ/1e6} MHz")

def read_packet():
    irq = read_reg(REG_IRQ_FLAGS)
    if irq & 0x40:  # RxDone
        write_reg(REG_IRQ_FLAGS, 0x40)

        if irq & 0x20:
            print("CRC error")
            write_reg(REG_IRQ_FLAGS, 0x20)
            return

        addr = read_reg(REG_FIFO_RX_CURRENT_ADDR)
        write_reg(REG_FIFO_ADDR_PTR, addr)
        length = read_reg(REG_RX_NB_BYTES)

        payload = [read_reg(REG_FIFO) for _ in range(length)]
        snr = read_reg(REG_PKT_SNR_VALUE)
        if snr & 0x80:
            snr = -(((~snr + 1) & 0xFF) >> 2)
        else:
            snr = (snr & 0xFF) >> 2

        rssi = read_reg(REG_PKT_RSSI_VALUE) - 157

        msg = bytes(payload)
        b64 = base64.b64encode(msg).decode()

        print(f"RSSI: {rssi} dBm | SNR: {snr} dB | Len: {length}")
        print(f"Payload (ascii): {msg.decode(errors='ignore')}")
        print(f"Payload (base64): {b64}")
        print("-" * 60)

# ================= RUN =================
reset_lora()
setup_lora()

while True:
    read_packet()
    time.sleep(0.01)
