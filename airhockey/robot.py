import socket
import struct


class Robot(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.destination = None

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()

    def delta(self, delta):
        pass

    def move(self, dst):
        x, y = dst
        self.destination = dst
        self.sock.sendto(struct.pack('<ii', x, y), (self.host, self.port))

