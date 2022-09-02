from typing import Tuple


class WorldToFrameTranslator(object):
    def __init__(self, frame_size, table_size):
        self.frame_width, self.frame_height = frame_size
        self.table_width, self.table_height = table_size
        self.horizontal_margin = 10
        frame_field_width = self.frame_width - self.horizontal_margin * 2
        frame_field_height = frame_field_width / 2
        self.vertical_margin = (self.frame_height - frame_field_height) / 2
        self.horizontal_ratio = self.table_width / frame_field_width
        self.vertical_ratio = self.table_height / frame_field_height

    def w2f(self, w: Tuple[float, float]) -> Tuple[int, int]:
        f_x = int(w[0] / self.horizontal_ratio + self.horizontal_margin)
        f_y = int(w[1] / self.vertical_ratio + self.vertical_margin)
        return f_x, f_y

    def f2w(self, f: Tuple[int, int]) -> Tuple[float, float]:
        w_x = (f[0] - self.horizontal_margin) * self.horizontal_ratio
        w_y = (f[1] - self.vertical_margin) * self.vertical_ratio
        return w_x, w_y
