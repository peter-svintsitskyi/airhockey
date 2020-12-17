import time


class Timeout(object):
    def __init__(self, delay):
        self.delay = delay
        self.t = time.time()

    def start(self):
        self.t = time.time()

    def timeout(self):
        if time.time() - self.t >= self.delay:
            self.t = time.time()
            return True
        return False
