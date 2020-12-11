import cv2
import abc
import numpy as np
from airhockey.debug import DebugWindow
from typing import Optional
from airhockey.vision.color import ColorRange, ColorDetector
from airhockey.vision.video import FrameReader


class Query(object):
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def execute(self, hsv, translator, debug_window): raise NotImplementedError

    @abc.abstractmethod
    def draw(self, frame): raise NotImplementedError


class VerifyPositionQuery(Query):
    NOT_DETECTED = "NO_SUCH_COLOR"
    OUT_OF_POSITION = "OUT_OF_POSITION"
    SUCCESS = "SUCCESS"

    def __init__(self, color: ColorRange, positions: list):
        self.color = color
        self.positions = positions
        self.detected_positions = []

    def __eq__(self, other):
        return self.color == other.color and self.positions == other.positions

    def execute(self, frame_hsv, translator, debug_window):
        detector = ColorDetector(color_range=self.color, translator=translator)
        self.detected_positions = detector.get_positions(frame_hsv, len(self.positions), debug_window.frame)

        if len(self.detected_positions) != len(self.positions):
            return self.NOT_DETECTED
        else:
            if sorted(self.detected_positions) == sorted(self.positions):
                return self.SUCCESS

            return self.OUT_OF_POSITION

    def draw(self, debug_window):
        for p in self.detected_positions:
            debug_window.draw_circle(world_coordinates=p,
                                     color=((self.color.h_low + self.color.h_high) / 2, self.color.sv_low, 255))
        for p in self.positions:
            debug_window.draw_circle(world_coordinates=p,
                                     color=((self.color.h_low + self.color.h_high) / 2, self.color.sv_low, 255))


class QueryContext(object):
    def __init__(self, *, translator, frame_reader: FrameReader, debug_window: Optional[DebugWindow]):
        self.translator = translator
        self.frame_reader = frame_reader
        self.frame = None
        self.frame_hsv = None
        self.debug_window = debug_window
        self.queries = []

    def __enter__(self):
        self.frame = self.frame_reader.read()
        self.frame_hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        kernel = np.ones((5, 5), np.uint8)
        # self.frame_hsv = cv2.dilate(self.frame_hsv, kernel, iterations=1)
        self.queries = []
        if self.debug_window is not None:
            self.debug_window.set_frame(self.frame, self.frame_hsv)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.debug_window is not None:
            self.debug_window.draw(self.queries)
        self.frame = None
        self.frame_hsv = None

    def query(self, query: Query) -> str:
        self.queries.append(query)
        return query.execute(self.frame_hsv, self.translator, self.debug_window)


