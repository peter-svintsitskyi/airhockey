from unittest import TestCase

import airhockey
from airhockey.handlers.detect_players import DetectPlayersHandler
from airhockey.vision.color import ColorRange
from airhockey.vision.query import VerifyPresenceQuery
from airhockey_tests.helpers import init_spy_log_handler, QueryContextMock


class TestDetectPlayersHandler(TestCase):
    def setUp(self):
        self.handler_tries_count = 3
        self.query_context = QueryContextMock()
        self.log_spy = init_spy_log_handler(
            airhockey.handlers.detect_players.__name__)
        self.puck_color_range = ColorRange(name="puck color range", h_low=1,
                                           h_high=2, sv_low=3)
        self.robot_pusher_color_range = ColorRange(
            name="robot pusher color range", h_low=4, h_high=5, sv_low=6)
        self.handler = DetectPlayersHandler(
            vision_query_context=self.query_context,
            puck_color_range=self.puck_color_range,
            robot_pusher_color_range=self.robot_pusher_color_range,
            tries=self.handler_tries_count,
            delay=0)

    def test_fails_when_puck_was_not_detected(self):
        self.query_context.mock_query_results([
            VerifyPresenceQuery.NOT_PRESENT,
            VerifyPresenceQuery.NOT_PRESENT,
            VerifyPresenceQuery.NOT_PRESENT,
            VerifyPresenceQuery.NOT_PRESENT,
            VerifyPresenceQuery.NOT_PRESENT,
            VerifyPresenceQuery.NOT_PRESENT,
        ])
        handler_result = self.handler()
        self.assertEqual(DetectPlayersHandler.FAIL, handler_result)
        self.assertEqual(6, self.query_context.call_count)
        self.assertEqual(VerifyPresenceQuery(self.puck_color_range),
                         self.query_context.executed_queries[0])
        self.assertEqual(VerifyPresenceQuery(self.robot_pusher_color_range),
                         self.query_context.executed_queries[1])
        self.assertEqual([
            "Detecting a puck and a robot pusher...",
            "Puck not found.",
            "Detecting a puck and a robot pusher...",
            "Puck not found.",
            "Detecting a puck and a robot pusher...",
            "Puck not found."
        ], self.log_spy.messages)

    def test_fails_when_robot_pusher_was_not_detected(self):
        self.query_context.mock_query_results([
            VerifyPresenceQuery.NOT_PRESENT,  # puck
            VerifyPresenceQuery.NOT_PRESENT,  # robot pusher
            VerifyPresenceQuery.PRESENT,  # puck
            VerifyPresenceQuery.NOT_PRESENT,  # robot pusher
            VerifyPresenceQuery.PRESENT,  # puck
            VerifyPresenceQuery.NOT_PRESENT,  # robot pusher
        ])
        handler_result = self.handler()
        self.assertEqual(DetectPlayersHandler.FAIL, handler_result)
        self.assertEqual(6, self.query_context.call_count)
        self.assertEqual(VerifyPresenceQuery(self.puck_color_range),
                         self.query_context.executed_queries[0])
        self.assertEqual(VerifyPresenceQuery(self.robot_pusher_color_range),
                         self.query_context.executed_queries[1])
        self.assertEqual([
            "Detecting a puck and a robot pusher...",
            "Puck not found.",
            "Detecting a puck and a robot pusher...",
            "Puck OK.",
            "Robot pusher not found.",
            "Detecting a puck and a robot pusher...",
            "Puck OK.",
            "Robot pusher not found."
        ], self.log_spy.messages)

    def test_success_when_both_puck_and_robot_pusher_detected(self):
        self.query_context.mock_query_results([
            VerifyPresenceQuery.NOT_PRESENT,  # puck
            VerifyPresenceQuery.NOT_PRESENT,  # robot pusher
            VerifyPresenceQuery.PRESENT,  # puck
            VerifyPresenceQuery.NOT_PRESENT,  # robot pusher
            VerifyPresenceQuery.PRESENT,  # puck
            VerifyPresenceQuery.PRESENT,  # robot pusher
        ])
        handler_result = self.handler()
        self.assertEqual(DetectPlayersHandler.SUCCESS, handler_result)
        self.assertEqual([
            "Detecting a puck and a robot pusher...",
            "Puck not found.",

            "Detecting a puck and a robot pusher...",
            "Puck OK.",
            "Robot pusher not found.",

            "Detecting a puck and a robot pusher...",
            "Puck OK.",
            "Robot pusher OK."
        ], self.log_spy.messages)
