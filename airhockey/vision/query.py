import cv2
import abc

import numpy as np

from airhockey.debug import DebugWindow
from typing import Optional, Tuple, List, Any

from airhockey.translate import WorldToFrameTranslator
from airhockey.vision.color import ColorRange, ColorDetector
from airhockey.vision.video import FrameReader


class Query(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def execute(
            self,
            hsv,
            translator: WorldToFrameTranslator,
            debug_window
    ): raise NotImplementedError

    @abc.abstractmethod
    def draw(self, frame): raise NotImplementedError


class PositionQuery(Query):
    def __init__(self, color_range: ColorRange):
        self.color_range = color_range
        self.detector = ColorDetector(color_range=self.color_range)

    def execute(self, hsv, translator: WorldToFrameTranslator, debug_window):
        positions = self.detector.get_positions(hsv, 1)
        if len(positions) > 0:
            return translator.f2w(positions[0])
        return None

    def draw(self, debug_window):
        ...


class VerifyPresenceQuery(Query):
    NOT_PRESENT = "NOT_PRESENT"
    PRESENT = "PRESENT"

    def __init__(self, color_range: ColorRange):
        self.color_range = color_range
        self.detector = ColorDetector(color_range=self.color_range)

    def execute(self, hsv, translator: WorldToFrameTranslator, debug_window):
        if len(self.detector.get_positions(hsv, 1)) > 0:
            return self.PRESENT

        return self.NOT_PRESENT

    def draw(self, frame):
        pass

    def __eq__(self, other):
        return self.color_range == other.color_range

    def __repr__(self):
        return "{n}(color_range={r})".format(n=__class__, r=self.color_range)


class VerifyPositionQuery(Query):
    NOT_DETECTED = "NOT_DETECTED"
    OUT_OF_POSITION = "OUT_OF_POSITION"
    SUCCESS = "SUCCESS"

    def __init__(
            self,
            color: ColorRange,
            expected_positions: List[Tuple[float, float]]
    ) -> None:
        self.color = color
        self.expected_positions = expected_positions
        self.detected_positions: List[Tuple[float, float]] = []
        self.detector = ColorDetector(color_range=self.color)

    def __eq__(self, other):
        return self.color == other.color and \
               self.expected_positions == other.expected_positions

    def execute(self, hsv, translator: WorldToFrameTranslator, debug_window):
        self.detected_positions = [
            translator.f2w(f)
            for f in self.detector.get_positions(
                hsv,
                len(self.expected_positions)
            )
        ]

        if len(self.detected_positions) != len(self.expected_positions):
            return self.NOT_DETECTED
        else:
            if self.close_to_detected():
                return self.SUCCESS

            return self.OUT_OF_POSITION

    def close_to_detected(self) -> bool:
        tol = 15.0
        for e in self.expected_positions:
            found = False
            for d in self.detected_positions:
                if abs(e[0] - d[0]) < tol and abs(e[1] - d[1]) < tol:
                    found = True
                    break
            if not found:
                return False
        return True

    def draw(self, debug_window):
        for p in self.detected_positions:
            debug_window.draw_circle(
                world_coordinates=p,
                color=((self.color.h_low + self.color.h_high) / 2,
                       self.color.sv_low, 255))
        for p in self.expected_positions:
            debug_window.draw_circle(
                world_coordinates=p,
                color=((self.color.h_low + self.color.h_high) / 2,
                       self.color.sv_low, 255))


class QueryContext(object):
    def __init__(self, *, translator: WorldToFrameTranslator, frame_reader: FrameReader,
                 markers_color_range: ColorRange,
                 debug_window: Optional[DebugWindow]):
        self.translator = translator
        self.frame_reader = frame_reader
        self.frame = None
        self.frame_hsv = None
        self.debug_window = debug_window
        self.queries: List = []
        self.can_execute = False
        self.dectector = ColorDetector(color_range=markers_color_range)

    def __enter__(self):
        self.frame = self.frame_reader.read()
        self.frame_hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        self.queries = []
        if self.debug_window is not None:
            self.debug_window.set_frame(self.frame, self.frame_hsv)
        self.can_execute = True

        markers = self.dectector.get_positions(self.frame_hsv, 4)
        if len(markers) < 4:
            return self

        markers = self._sort_markers(
            np.float32([[a, b] for (a, b) in markers]))

        dst = np.float32(
            [
                [0, 0],
                [1200, 0],
                [1200, 600],
                [0, 600]
            ]
        )

        transform = cv2.getPerspectiveTransform(markers, dst)

        if self.debug_window is not None:
            self.debug_window.set_frame(self.frame, self.frame_hsv)

        if np.linalg.matrix_rank(transform) != 3:
            return self

        self.translator.frame_to_world = transform
        self.translator.world_to_frame = np.linalg.inv(
            self.translator.frame_to_world)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.can_execute = False
        if self.debug_window is not None:
            self.debug_window.draw(self.queries, self.frame_reader)
        self.frame = None
        self.frame_hsv = None

    def query(self, query: Query) -> Any:
        if not self.can_execute:
            raise RuntimeError(
                'Cannot execute a query from inactive context')
        self.queries.append(query)
        return query.execute(
            self.frame_hsv, self.translator, self.debug_window)

    def _sort_markers(self, markers):
        result = np.zeros((4, 2), dtype="float32")
        s = markers.sum(axis=1)
        result[0] = markers[np.argmin(s)]
        result[2] = markers[np.argmax(s)]
        diff = np.diff(markers, axis=1)
        result[1] = markers[np.argmin(diff)]
        result[3] = markers[np.argmax(diff)]
        return result
