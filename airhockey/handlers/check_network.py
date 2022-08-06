import logging
import select
import socket


class CheckNetworkHandler(object):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"

    def __init__(self, *, host, port: int, tries, delay):
        self.host = host
        self.port = port
        self.tries = tries
        self.delay = delay
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def __call__(self, *args, **kwargs):
        for i in range(self.tries):
            self.logger.info(f"Pinging {self.host}:{self.port}...")
            client = socket.socket(family=socket.AF_INET,
                                   type=socket.SOCK_DGRAM)
            client.sendto(b"ping", (self.host, self.port))
            r, _, _ = select.select([client], [], [], self.delay)
            if r:
                message, address = client.recvfrom(1024)
                if message != b"pong airhockey":
                    self.logger.info("Failed.")
                else:
                    self.logger.info("Ping OK.")
                    client.close()
                    return self.SUCCESS
            else:
                self.logger.info("Failed.")

            client.close()

        return self.FAIL
