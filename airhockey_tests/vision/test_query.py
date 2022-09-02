import unittest
from typing import Tuple, List

from airhockey.translate import WorldToFrameTranslator
from airhockey.vision.color import ColorRange, ColorDetector
from airhockey.vision.query import VerifyPositionQuery, VerifyPresenceQuery


class FakeDetector(ColorDetector):
    def __init__(
            self,
            what_to_return: List[Tuple[float, float]]
    ) -> None:
        self.what_to_return = what_to_return

    def get_positions(
            self,
            hsv,
            number_of_results
    ) -> List[Tuple[float, float]]:
        return self.what_to_return


class AddFiftyFakeTranslator(WorldToFrameTranslator):
    def __init__(self):
        ...

    def w2f(self, w: Tuple[float, float]) -> Tuple[int, int]:
        return (
            int(w[0] - 50),
            int(w[1] - 50)
        )

    def f2w(self, f: Tuple[int, int]) -> Tuple[float, float]:
        return (
            f[0] + 50,
            f[1] + 50
        )


class TestVerifyPositionQuery(unittest.TestCase):
    def test_not_detected_when_number_of_detected_points_dont_match(self):
        query = self._create_query(
            expected_world_positions=[(0, 0), (100, 100)],
            detected_frame_positions=[(0, 0)]
        )
        self.assertEqual(
            VerifyPositionQuery.NOT_DETECTED,
            self._execute_query(query)
        )

    def test_success_when_exact_points(self):
        query = self._create_query(
            expected_world_positions=[(50, 50), (150, 150)],
            detected_frame_positions=[(0, 0), (100, 100)]
        )
        self.assertEqual(
            VerifyPositionQuery.SUCCESS,
            self._execute_query(query)
        )

    def test_success_when_points_in_different_order(self):
        query = self._create_query(
            expected_world_positions=[(50, 50), (150, 150), (250, 250)],
            detected_frame_positions=[(200, 200), (0, 0), (100, 100)]
        )
        self.assertEqual(
            VerifyPositionQuery.SUCCESS,
            self._execute_query(query)
        )

    def test_success_when_points_within_tollerance(self):
        t = 0.1
        query = self._create_query(
            expected_world_positions=[(50, 50), (150, 150), (250, 250)],
            detected_frame_positions=[
                (200 + t, 200 - t),
                (0 - t, 0 + t),
                (100 + t, 100 - t)
            ]
        )
        self.assertEqual(
            VerifyPositionQuery.SUCCESS,
            self._execute_query(query)
        )

    def test_out_of_position(self):
        query = self._create_query(
            expected_world_positions=[(50, 50), (150, 150), (250, 250)],
            detected_frame_positions=[(210, 210), (1, 10), (300, 300)]
        )
        self.assertEqual(
            VerifyPositionQuery.OUT_OF_POSITION,
            self._execute_query(query)
        )

    def _execute_query(self, query):
        return query.execute(None, AddFiftyFakeTranslator(), None)

    def _create_query(
            self,
            *,
            expected_world_positions: List[Tuple[float, float]],
            detected_frame_positions: List[Tuple[float, float]]
    ) -> VerifyPositionQuery:
        query = VerifyPositionQuery(
            color=ColorRange(name="test", h_low=0, h_high=255, sv_low=0),
            expected_positions=expected_world_positions
        )
        query.detector = FakeDetector(detected_frame_positions)
        return query


class TestVerifyPresenceQuery(unittest.TestCase):
    def test_not_present(self):
        query = VerifyPresenceQuery(
            color_range=ColorRange(name="test", h_low=0, h_high=255, sv_low=0)
        )
        query.detector = FakeDetector([])
        result = query.execute(None, AddFiftyFakeTranslator(), None)
        self.assertEqual(VerifyPresenceQuery.NOT_PRESENT, result)

    def test_present(self):
        query = VerifyPresenceQuery(
            color_range=ColorRange(name="test", h_low=0, h_high=255, sv_low=0)
        )
        query.detector = FakeDetector([(100, 100), (200, 200)])
        result = query.execute(None, AddFiftyFakeTranslator(), None)
        self.assertEqual(VerifyPresenceQuery.PRESENT, result)
