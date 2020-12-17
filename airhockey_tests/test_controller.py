import unittest
from airhockey.controller import *


def foo_handler():
    return "foo"


def none_handler():
    return None


class TestStateHandler(unittest.TestCase):
    def test_state_handler_executed(self):
        executed1 = False

        def handler1():
            nonlocal executed1
            executed1 = True

        executed2 = False

        def handler2():
            nonlocal executed2
            executed2 = True

        c = Controller("state", "state")
        c.register_handler("state", handler1)
        c.register_handler("state", handler2)
        c.run()
        self.assertTrue(executed1)
        self.assertTrue(executed2)

    def test_switched_to_state_returned_by_handler(self):
        c = Controller("state", "FakeState")
        c.register_handler("state", foo_handler, {"foo": "FakeState"})
        c.register_handler("FakeState", none_handler, {})
        c.run()
        self.assertEqual(c.get_state(), "FakeState")

    def test_exception_raised_when_multiple_handlers_return_new_state(self):
        c = Controller("state", "state")
        c.register_handler("state", foo_handler, {"foo": "FakeState"})
        c.register_handler("state", foo_handler, {"foo": "FakeState"})
        with self.assertRaises(RunHandlerException) as context:
            c.run()
