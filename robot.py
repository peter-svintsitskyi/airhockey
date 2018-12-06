import socket
import json
import time
import math
import sys


class Robot(object):
    def __init__(self):
        self.destination_x = None
        self.destination_y = None
        self.current_x = 0
        self.current_y = 0
        self.move_start_time = 0
        self.velocity = 200

    def handle(self, command):
        if self.move_start_time > 0:
            dt = time.time() - self.move_start_time
            dx = self.destination_x - self.current_x
            dy = self.destination_y - self.current_y

            to_go = math.sqrt(dx * dx + dy * dy)
            velocity_dt = self.velocity * dt

            if to_go < velocity_dt:
                k = 1
            else:
                k = to_go / velocity_dt

            self.current_x += dx / k
            self.current_y += dy / k

            if abs(self.current_x - self.destination_x) < 0.1 and abs(self.current_y - self.destination_y) < 0.1:
                self.move_start_time = 0

        else:
            move = command.get("move")

            if move is not None:
                self.destination_x = move["x"]
                self.destination_y = move["y"]
                self.move_start_time = time.time()

                print("Moving to: {x}, {y}".format(x=self.destination_x, y=self.destination_y))

        return {
            "x": self.current_x,
            "y": self.current_y
        }


if __name__ == "__main__":
    r = Robot()

    HOST, PORT = "0.0.0.0", 9998

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.bind((HOST, PORT))
    except socket.error as msg:
        print(msg)
        sys.exit()

    s.listen(10)

    try:
        while True:
            conn, addr = s.accept()

            while True:
                data = conn.recv(1024).strip()

                if len(data) == 0:
                    break

                line = data.decode('utf-8')

                response = r.handle(json.loads(line))

                conn.send(json.dumps(response).encode('utf-8'))
    finally:
        s.close()
