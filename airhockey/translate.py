from airhockey.geometry import Point, PointF


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

    def w2f(self, w: PointF):
        f_x = int(w.x / self.horizontal_ratio + self.horizontal_margin)
        f_y = int(w.y / self.vertical_ratio + self.vertical_margin)
        return Point(f_x, f_y)

    def f2w(self, f: Point):
        w_x = (f.x - self.horizontal_margin) * self.horizontal_ratio
        w_y = (f.y - self.vertical_margin) * self.vertical_ratio
        return PointF(w_x, w_y)
