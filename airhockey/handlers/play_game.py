import logging
import math
from typing import Tuple

from airhockey.robot import Robot
from airhockey.trajectory import Trajectory
from airhockey.vision.color import ColorRange
from airhockey.vision.query import QueryContext, PositionQuery


class PlayGameHandler:
    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'

    def __init__(
            self,
            *,
            robot: Robot,
            vision_query_context: QueryContext,
            puck_color_range: ColorRange,
            pusher_color_range: ColorRange,
            puck_workspace: Tuple[float, float]
    ):
        self.robot = robot
        self.vision_query_context = vision_query_context
        self.puck_color_range = puck_color_range
        self.pusher_color_range = pusher_color_range
        self.logger = logging.getLogger(__name__)
        self.trajectory = Trajectory(puck_workspace)

    def __call__(self, *args, **kwargs):
        """
        [X] 1. See puck position
        2. Calculate puck velocity
        3. Calculate puck trajectory
        [X] 4. See pusher position
        5. Move pusher to the interception point
        """
        self.logger.info("Starting game")

        with self.robot:
            while True:
                with self.vision_query_context as context:
                    puck_position = context.query(
                        PositionQuery(color_range=self.puck_color_range)
                    )
                    pusher_position = context.query(
                        PositionQuery(color_range=self.pusher_color_range)
                    )

                    if puck_position is None:
                        print("No puck")
                        continue

                    if pusher_position is None:
                        print("No pusher")
                        continue

                    self.trajectory.register_position(puck_position)

                    interception_points = self.trajectory.\
                        calculate_interception_points()
                    if interception_points:
                        dx = puck_position[0] - pusher_position[0]
                        dy = puck_position[1] - pusher_position[1]
                        distance_to_puck = math.sqrt(pow(dx, 2) + pow(dy, 2))

                        if (distance_to_puck < 200):
                            self.robot.move(
                                (int(pusher_position[0] + dx * 4),
                                 int(pusher_position[1] + dy * 4)))
                        else:
                            self.robot.move(interception_points[0])

        return self.FAIL
