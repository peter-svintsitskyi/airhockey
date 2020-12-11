

class Point(object):
    def __init__(self, *args):
        if len(args) == 1:
            self.x, self.y = args[0]
        else:
            self.x = args[0]
            self.y = args[1]

    def tuple(self):
        return self.x, self.y

    def __repr__(self):
        return "PointF({x};{y})".format(x=self.x, y=self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __lt__(self, other):
        if self.x < other.x:
            return True
        if self.y < other.y:
            return True
        return False


class PointF(Point):
    DELTA = 5.0

    def __eq__(self, other):
        if abs(self.x - other.x) > self.DELTA:
            return False
        if abs(self.y - other.y) > self.DELTA:
            return False
        return True
