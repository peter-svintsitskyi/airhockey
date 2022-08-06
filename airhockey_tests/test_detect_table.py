import unittest
import logging
import numpy
from unittest.mock import MagicMock
import airhockey
from airhockey.vision.video import FrameReader
from airhockey.vision.color import ColorRange
from airhockey.vision.query import QueryContext, VerifyPositionQuery
from airhockey.handlers.detect_table import DetectTableHandler
from airhockey_tests.helpers import init_spy_log_handler


class TestDetectTableHandler(unittest.TestCase):
    def setUp(self):
        self.log_spy = init_spy_log_handler(
            airhockey.handlers.detect_table.__name__)

    def make_calibrate_handler(self, *, tries, delay):
        self.grabbed_frame = numpy.zeros((100, 100, 3), numpy.uint8)
        self.frame_reader = FrameReader()
        self.frame_reader.read = MagicMock(return_value=self.grabbed_frame)
        self.expected_markers = [(0, 500), (600, 600)]
        self.query_context = QueryContext(translator=None,
                                          frame_reader=self.frame_reader,
                                          debug_window=None)
        self.color_range = ColorRange(name="", h_low=0, h_high=0, sv_low=0)
        self.calibrate_handler = DetectTableHandler(
            expected_markers=self.expected_markers,
            color_range=self.color_range,
            vision_query_context=self.query_context,
            tries=tries,
            delay=delay)

    def test_handler_returns_failure_when_no_markers_detected(self):
        self.make_calibrate_handler(tries=3, delay=0)
        logger = logging.getLogger(airhockey.handlers.detect_table.__name__)
        self.assertEqual(logging.INFO, logger.getEffectiveLevel())

        expected_query = VerifyPositionQuery(self.color_range,
                                             self.expected_markers)

        self.query_context.query = MagicMock(
            return_value=VerifyPositionQuery.NOT_DETECTED)
        self.assertEqual(DetectTableHandler.FAIL, self.calibrate_handler())
        self.assertListEqual(
            [
                "Detecting table...",
                "Could not see table markers.",
                "Detecting table...",
                "Could not see table markers.",
                "Detecting table...",
                "Could not see table markers.",
            ],
            self.log_spy.messages
        )
        self.assertGreater(self.frame_reader.read.call_count, 3)
        self.assertGreater(self.query_context.query.call_count, 3)
        self.query_context.query.assert_called_with(expected_query)

    def test_can_configure_number_of_retries_and_delay(self):
        self.make_calibrate_handler(tries=2, delay=0.01)
        self.query_context.query = MagicMock(
            return_value=VerifyPositionQuery.NOT_DETECTED)
        self.assertEqual(DetectTableHandler.FAIL, self.calibrate_handler())
        self.assertListEqual(
            [
                "Detecting table...",
                "Could not see table markers.",
                "Detecting table...",
                "Could not see table markers.",
            ],
            self.log_spy.messages
        )

    def test_returns_failure_when_markers_detected_in_wrong_position(self):
        self.make_calibrate_handler(tries=1, delay=0)
        self.query_context.query = MagicMock(
            return_value=VerifyPositionQuery.OUT_OF_POSITION)
        self.assertEqual(DetectTableHandler.FAIL, self.calibrate_handler())
        self.assertListEqual(
            [
                "Detecting table...",
                "Table markers are out of position.",
            ],
            self.log_spy.messages
        )

    def test_returns_success_when_markers_are_in_correct_position(self):
        self.make_calibrate_handler(tries=1, delay=0)
        self.query_context.query = MagicMock(
            return_value=VerifyPositionQuery.SUCCESS)
        self.assertEqual(DetectTableHandler.SUCCESS, self.calibrate_handler())
        self.assertListEqual(
            [
                "Detecting table...",
                "Table markers detected.",
            ],
            self.log_spy.messages
        )
