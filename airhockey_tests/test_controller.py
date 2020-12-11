import unittest
from airhockey.controller import *


class FakeState(ControllerState):
    pass


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

        c = Controller()
        c.register_handler(IdleControllerState, handler1)
        c.register_handler(IdleControllerState, handler2)
        c.run()
        self.assertTrue(executed1)
        self.assertTrue(executed2)

    def test_switched_to_state_returned_by_handler(self):
        def handler():
            return "foo"

        c = Controller()
        c.register_handler(IdleControllerState, handler, {"foo": FakeState})
        c.run()
        self.assertIsInstance(c.get_state(), FakeState)

    def test_exception_raised_when_multiple_handlers_return_new_state(self):
        def handler():
            return "foo"

        c = Controller()
        c.register_handler(IdleControllerState, handler, {"foo": FakeState})
        c.register_handler(IdleControllerState, handler, {"foo": FakeState})
        with self.assertRaises(RunHandlerException) as context:
            c.run()


class TestControllerStartProcedure(unittest.TestCase):
    def setUp(self):
        self.controller = Controller()

    def test_state_is_idle_when_new_instance_created(self):
        self.assertIsInstance(self.controller.get_state(), IdleControllerState)

    def test_calibration_procedure_executed_when_started(self):
        self.controller.start()
        self.assertIsInstance(self.controller.get_state(), CalibrateControllerState)

    def test_exception_raised_if_started_when_not_idle(self):
        self.controller.start()
        with self.assertRaises(IllegalStateSwitchException) as context:
            self.controller.start()


