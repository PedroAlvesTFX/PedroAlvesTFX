from camera import Camera

cam = Camera()

print()

print("Camera OK")

print()

while True:

    frame = cam.read()

    print(frame.shape)