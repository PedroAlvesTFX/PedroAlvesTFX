import serial
import time
import sys

def createMyDevice():

    for i in range(5):
        device = str(f"/dev/ttyACM{i}")
        try:
            ser = serial.Serial(device, 9600, timeout=1)
            time.sleep(2)
            return True, device, ser
        except:
            pass

    return False, None, None

def checkDevice(isCreated: bool, device: str, ser):

    if isCreated:
        print(f"NewDeviceConnected: {device}")
        return True, ser 
    else:
        while True:
            try: 
                inputted = int(input("Connection ERROR, digite 0 para sair e 1 para tentar novamente"))

                if inputted == 0:
                    sys.exit(1)
                elif inputted == 1:
                    isCreated, device, ser = createMyDevice()
                    try:
                        ser.write("\n".encode())
                        print(f"NewDeviceConnected: {device}")
                        return True, ser
                    except serial.SerialException:
                        print("device is not created, reset loop...")
            except ValueError:
                print("Digite apenas 0 ou 1")

def mainLoop():

    global isCreated
    global ser

    while(1):
        msg = ""
        while(1):
            try:
                msg = str(input("Digite o angulo no modelo (\"E123\")--> "))
                if len(msg) > 0:
                    ser.write(msg.strip().encode())
                    ang = msg[1:4]
                    print(f"Servo {ang} graus")
                    break
            except serial.SerialException:

                print("Device desconectado")
                isCreated, ser = checkDevice(*createMyDevice())
                
    #if ser.in_waiting:
        #print(ser.readline().decode(errors="ignore").strip())


isCreated, ser = checkDevice(*createMyDevice())

ser.write("E090".encode())
print("Servo 90 graus")


mainLoop()

