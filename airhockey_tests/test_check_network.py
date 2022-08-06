import socket
import threading
import unittest
import airhockey
from airhockey.handlers.check_network import CheckNetworkHandler
from airhockey_tests.helpers import init_spy_log_handler


def fake_server(response: bytes) -> threading.Thread:
    def loop():
        server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        server.bind(('127.0.0.1', 9988))

        print("SERVER READY")

        while True:
            message, address = server.recvfrom(1024)
            print("Message from Client:{}".format(message))
            print("Client address:{}".format(address))
            server.sendto(response, address)
            server.close()
            break

    thread = threading.Thread(target=loop)
    thread.start()

    return thread


class TestCheckNetworkHandler(unittest.TestCase):
    def setUp(self):
        self.log_spy = init_spy_log_handler(
            airhockey.handlers.check_network.__name__)
        self.robot_host = '127.0.0.1'
        self.robot_port = 9988

    def testFailedConnection(self):
        handler = CheckNetworkHandler(
            host=self.robot_host, port=self.robot_port, tries=3, delay=0.1)
        self.assertEqual(CheckNetworkHandler.FAIL, handler())
        self.assertEqual([
            f"Pinging {self.robot_host}:{self.robot_port}...",
            "Failed.",
            f"Pinging {self.robot_host}:{self.robot_port}...",
            "Failed.",
            f"Pinging {self.robot_host}:{self.robot_port}...",
            "Failed.",
        ], self.log_spy.messages)

    def testFailedWhenServerResponseIsIncorrect(self):
        server_thread = fake_server(b"foo")

        handler = CheckNetworkHandler(
            host=self.robot_host, port=self.robot_port, tries=1, delay=0)
        result = handler()

        server_thread.join()

        self.assertEqual(CheckNetworkHandler.FAIL, result)
        self.assertEqual([
            f"Pinging {self.robot_host}:{self.robot_port}...",
            "Failed.",
        ], self.log_spy.messages)

    def testSuccessfulConnection(self):
        server_thread = fake_server(b"pong airhockey")

        handler = CheckNetworkHandler(
            host=self.robot_host, port=self.robot_port, tries=1, delay=0.1)
        result = handler()

        server_thread.join()

        self.assertEqual(CheckNetworkHandler.SUCCESS, result)
        self.assertEqual([
            f"Pinging {self.robot_host}:{self.robot_port}...",
            "Ping OK.",
        ], self.log_spy.messages)
