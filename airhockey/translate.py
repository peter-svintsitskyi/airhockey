from typing import Tuple

import cv2
import numpy as np


class WorldToFrameTranslator(object):
    def __init__(self, video_size, table_size):
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
        print("INIT!")
        self.frame_to_world = np.eye(3)
        self.world_to_frame = np.eye(3)

    def w2f(self, w: Tuple[float, float]) -> Tuple[int, int]:
        res = np.int32(cv2.perspectiveTransform(
            np.float32([[w[0], w[1]]])[None, :, :],
            self.world_to_frame
        ).reshape((-1, 2))[0])
        return res

    def f2w(self, f: Tuple[int, int]) -> Tuple[float, float]:
        res = np.float32(cv2.perspectiveTransform(
            np.float32([[f[0], f[1]]])[None, :, :],
            self.frame_to_world
        ).reshape((-1, 2))[0])
        return res
