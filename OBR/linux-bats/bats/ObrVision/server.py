from camera import Camera
from server import Server

camera = Camera()

server = Server(camera)

print()

print("===================================")
print(" OBR Vision")
print("===================================")

server.run()