import socket
import struct


class Robot(object):
    def __init__(self, *, host, port):
        self.host = host
        self.port = port
        self.destination = None
        self.can_move = False

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.can_move = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.can_move = False
        self.sock.close()

    def delta(self, delta):
        pass

    def move(self, dst):
        if not self.can_move:
            raise RuntimeError(
                'Cannot move robot when the context is not active')
        x, y = dst
        self.destination = dst
        self.sock.sendto(struct.pack('<ii', int(x), int(y)), (self.host, self.port))
