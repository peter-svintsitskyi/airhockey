import unittest
from typing import Tuple

import airhockey
from airhockey.handlers.test_moves import TestMovesHandler
from airhockey.robot import Robot
from airhockey.vision.color import ColorRange
from airhockey.vision.query import VerifyPositionQuery
from airhockey_tests.helpers import init_spy_log_handler, QueryContextMock


class RobotSpy(Robot):
    def __init__(self):
        self.destinations = []

    def move(self, destination: Tuple[float, float]):
        self.destinations.append(destination)


class TestTestMovesHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.log_spy = init_spy_log_handler(
            airhockey.handlers.test_moves.__name__)
        self.robot_spy = RobotSpy()
        self.query_context = QueryContextMock()
        self.robot_pusher_color_range = ColorRange(
            name="robot pusher color range", h_low=4, h_high=5, sv_low=6)
        self.destinations = [
            (300, 300),
            (50, 50),
            (550, 50),
            (550, 550),
            (50, 550),
            (50, 50),
            (300, 300),
        ]

    def test_does_test_moves(self):
        handler = TestMovesHandler(
            destinations=self.destinations,
            robot=self.robot_spy,
            vision_query_context=self.query_context,
            robot_pusher_color_range=self.robot_pusher_color_range,
            delay=0
        )

        self.query_context.mock_query_results(
            [VerifyPositionQuery.SUCCESS] * len(self.destinations)
        )

        result = handler()

        self.assertEqual(self.destinations, self.robot_spy.destinations)

        self.assertEqual(
            len(self.destinations), self.query_context.call_count)

        self.assertEqual(
            [VerifyPositionQuery(
                self.robot_pusher_color_range, [destination]
            ) for destination in self.destinations],
            self.query_context.executed_queries
        )

        self.assertEqual(
            [message for dst in self.destinations
             for message in [
                 f"Moving a robot pusher to ({dst[0]}, {dst[1]})",
                 "Vision has verified the position"
             ]],
            self.log_spy.messages
        )
        self.assertEqual(TestMovesHandler.SUCCESS, result)

    def test_fails_when_could_not_verify_a_position(self):
        handler = TestMovesHandler(
            destinations=self.destinations,
            robot=self.robot_spy,
            vision_query_context=self.query_context,
            robot_pusher_color_range=self.robot_pusher_color_range,
            delay=0
        )

        self.query_context.mock_query_results(
            [VerifyPositionQuery.SUCCESS,
             VerifyPositionQuery.SUCCESS,
             VerifyPositionQuery.OUT_OF_POSITION,
             VerifyPositionQuery.SUCCESS,
             VerifyPositionQuery.SUCCESS,
             VerifyPositionQuery.SUCCESS,
             VerifyPositionQuery.SUCCESS]
        )

        result = handler()

        self.assertEqual(TestMovesHandler.FAIL, result)
        self.assertEqual(self.destinations[:3], self.robot_spy.destinations)
        self.assertEqual(
            ['Moving a robot pusher to (300, 300)',
             'Vision has verified the position',
             'Moving a robot pusher to (50, 50)',
             'Vision has verified the position',
             'Moving a robot pusher to (550, 50)',
             'Vision has failed to verify the position'],
            self.log_spy.messages
        )
