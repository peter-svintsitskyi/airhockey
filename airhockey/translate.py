from typing import Tuple
import numpy as np


class WorldToFrameTranslator(object):
    def __init__(self, video_size, table_size):
        video_width, video_height = video_size
        table_width, table_height = table_size
        horizontal_margin = 32
        frame_width = video_width - horizontal_margin * 2
        frame_height = frame_width / 2
        vertical_margin = (video_height - frame_height) / 2

        ratio = table_width / frame_width

        self.frame_to_world = [
            [ratio,     0, -horizontal_margin],
            [0,     ratio,   -vertical_margin],
            [0,         0,              ratio],
        ]

        self.world_to_frame = np.linalg.inv(self.frame_to_world)

    def w2f(self, w: Tuple[float, float]) -> Tuple[int, int]:
        res = np.matmul(self.world_to_frame, [w[0], w[1], 1])
        return int(res[0]), int(res[1])

    def f2w(self, f: Tuple[int, int]) -> Tuple[float, float]:
        res = np.matmul(self.frame_to_world,  [f[0], f[1], 1])
        return res[0], res[1]
