from typing import Tuple, List

import cv2
import numpy as np

from airhockey.debug import DebugWindow
from airhockey.vision.color import ColorRange, ColorDetector


class Transform:
    def __init__(self):
        self.frame_to_world = np.eye(3)
        self.world_to_frame = np.eye(3)

    def w2f(self, w: Tuple[float, float]) -> Tuple[int, int]:
        res = np.array(cv2.perspectiveTransform(
            np.array([[w[0], w[1]]], dtype=np.float32)[None, :, :],
            self.world_to_frame
        ).reshape((-1, 2))[0], dtype=np.int32)
        return res[0], res[1]

    def f2w(self, f: Tuple[int, int]) -> Tuple[float, float]:
        res = np.array(cv2.perspectiveTransform(
            np.array([[f[0], f[1]]], dtype=np.float32)[None, :, :],
            self.frame_to_world,
        ).reshape((-1, 2))[0], dtype=np.float32)
        return res[0], res[1]


class Perspective(Transform):

    def __init__(
            self,
            *,
            markers_color_range: ColorRange,
            markers_world_positions: List
    ):
        # video_width, video_height = video_size
        # table_width, table_height = table_size
        # horizontal_margin = 32
        # frame_width = video_width - horizontal_margin * 2
        # frame_height = frame_width / 2
        # vertical_margin = (video_height - frame_height) / 2
        #
        # ratio = frame_width / table_width
        #
        # self.world_to_frame = [
        #     [ratio,     0,  horizontal_margin],
        #     [0,     ratio,    vertical_margin],
        #     [0,         0,              1],
        # ]
        #
        # self.frame_to_world = np.linalg.inv(self.world_to_frame)

        super().__init__()
        self.markers_world_positions = markers_world_positions
        self.detector = ColorDetector(color_range=markers_color_range)

    def update_transform(self, hsv):
        markers = self.detector.get_positions(hsv, 4)
        if len(markers) < 4:
            return

        markers = self._sort_markers(np.array([[a, b] for (a, b) in markers]))

        dst = np.float32(
            [
                [0, 0],
                [1200, 0],
                [1200, 600],
                [0, 600]
            ]
        )

        transform = cv2.getPerspectiveTransform(markers, dst)

        if np.linalg.matrix_rank(transform) != 3:
            return

        self.frame_to_world = transform
        self.world_to_frame = np.linalg.inv(self.frame_to_world)

        return self

    def _sort_markers(self, markers):
        result = np.zeros((4, 2), dtype="float32")
        s = markers.sum(axis=1)
        result[0] = markers[np.argmin(s)]
        result[2] = markers[np.argmax(s)]
        diff = np.diff(markers, axis=1)
        result[1] = markers[np.argmin(diff)]
        result[3] = markers[np.argmax(diff)]
        return result

    def draw(self, debug: DebugWindow):
        points = [self.w2f(p) for p in self.markers_world_positions]
        debug.draw_poly(points, (0, 255, 255))
