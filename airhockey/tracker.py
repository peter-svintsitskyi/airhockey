import math

import numpy as np
from sklearn import preprocessing


class Tracker(object):
    x = None
    y = None
    old_vector = None

    def direction(self, x, y):
        if self.x is None:
            self.x = x
            self.y = y
            return None

        dx = x - self.x
        dy = y - self.y

        velocity_square = dx * dx + dy * dy

        vector = preprocessing.normalize(
            np.asarray([dx, dy]).reshape(1, -1)
        )

        if velocity_square > 3000:
            self.old_vector = vector[0]
            self.x = x
            self.y = y

        if self.old_vector is None:
            return None

        return self.old_vector, math.sqrt(velocity_square)
