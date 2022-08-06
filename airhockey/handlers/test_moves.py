import logging
import time
from typing import Tuple, List

from airhockey.robot import Robot
from airhockey.vision.color import ColorRange
from airhockey.vision.query import QueryContext, VerifyPositionQuery


class TestMovesHandler:
    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'

    def __init__(
            self,
            *,
            destinations: List[Tuple[float, float]],
            robot: Robot,
            vision_query_context: QueryContext,
            robot_pusher_color_range: ColorRange,
            delay: float
    ):
        self.destinations = destinations
        self.robot = robot
        self.vision_query_context = vision_query_context
        self.robot_pusher_color_range = robot_pusher_color_range
        self.delay = delay
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def __call__(self, *args, **kwargs):
        with self.robot:
            with self.vision_query_context as context:
                for destination in self.destinations:
                    self._move(destination)
                    time.sleep(self.delay)
                    if not self._verify_pusher_position(context, destination):
                        return self.FAIL

        return self.SUCCESS

    def _verify_pusher_position(
            self,
            context: QueryContext,
            destination: Tuple[float, float]
    ) -> bool:
        query_result = context.query(VerifyPositionQuery(
            self.robot_pusher_color_range,
            [destination]
        ))
        if query_result == VerifyPositionQuery.SUCCESS:
            self.logger.info("Vision has verified the position")
            return True
        else:
            self.logger.info("Vision has failed to verify the position")
            return False

    def _move(self, dst):
        self.logger.info(f"Moving a robot pusher to ({dst[0]}, {dst[1]})")
        self.robot.move(dst)
