import math
from typing import Tuple, Optional

import numpy as np
from sklearn import preprocessing


def get_intersect(a1, a2, b1, b2):
    """
    Returns the point of intersection of the lines passing through a2,a1 and
    b2,b1.
    a1: [x, y] a point on the first line
    a2: [x, y] another point on the first line
    b1: [x, y] a point on the second line
    b2: [x, y] another point on the second line
    """

    s = np.vstack([a1, a2, b1, b2])  # s for stacked
    h = np.hstack((s, np.ones((4, 1))))  # h for homogeneous
    l1 = np.cross(h[0], h[1])  # get first line
    l2 = np.cross(h[2], h[3])  # get second line
    x, y, z = np.cross(l1, l2)  # point of intersection
    if z == 0:  # lines are parallel
        return (float('inf'), float('inf'))

    return (x / z, y / z)


class Trajectory:
    def __init__(self, workspace: Tuple[float, float]):
        self.workspace = workspace
        self.calculator = DirectionCalculator()
        self.position: Optional[Tuple[float, float]] = None
        self.direction = None

    def calculate_interception_points(self):
        interception_points = []

        if self.direction is None:
            return

        x_distance_between_intersection_points = 100
        x_start = 100
        x_end = int(self.position[0] / 2)
        for x in range(x_start, x_end, x_distance_between_intersection_points):
            intersection = self.intersect_puck_trajectory_at_x(x)
            if intersection is not None:
                interception_points.append(intersection)

        return interception_points

    def intersect_puck_trajectory_at_x(self, x):
        p_x, p_y = self.position
        v_x, v_y = self.direction
        intersection = get_intersect(
            (x, 0), (x, 1),
            self.position, (p_x + v_x, p_y + v_y)
        )
        i_x, i_y = intersection

        if i_x == float('inf'):
            return None

        n = int(i_y / self.workspace[1])
        if i_y < 0 or i_y > self.workspace[1]:
            i_y = abs(i_y) - abs(n * self.workspace[1])

            if n % 2 != 0:
                i_y = self.workspace[1] - i_y

        return i_x, i_y

    def register_position(
            self,
            position: Tuple[float, float]
    ):
        self.position = position
        self.direction, speed = self.calculator.direction(position)


class DirectionCalculator(object):
    def __init__(self):
        self.x = None
        self.y = None
        self.old_vector = None

    def direction(
            self,
            position: Tuple[float, float]
    ) -> Tuple:
        x, y = position
        if self.x is None:
            self.x = x
            self.y = y
            return None, None

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
            return None, None

        return self.old_vector, math.sqrt(velocity_square)
