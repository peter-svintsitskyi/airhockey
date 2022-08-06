import logging

from airhockey.utils import Timeout
from airhockey.vision.query import VerifyPresenceQuery


class DetectPlayersHandler(object):
    FAIL = "FAIL"
    SUCCESS = "SUCCESS"

    def __init__(
            self,
            *,
            vision_query_context,
            puck_color_range,
            robot_pusher_color_range,
            tries,
            delay
    ):
        self.vision_query_context = vision_query_context
        self.puck_color_range = puck_color_range
        self.robot_pusher_color_range = robot_pusher_color_range
        self.tries = tries
        self.delay = delay
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def __call__(self, *args, **kwargs):
        t = Timeout(self.delay)
        i = 0
        while True:
            with self.vision_query_context:
                puck = self.vision_query_context.query(
                    VerifyPresenceQuery(self.puck_color_range))
                robot_pusher = self.vision_query_context.query(
                    VerifyPresenceQuery(self.robot_pusher_color_range))

                if not t.timeout():
                    continue

                self.logger.info("Detecting a puck and a robot pusher...")
                if puck == VerifyPresenceQuery.NOT_PRESENT:
                    self.logger.info("Puck not found.")

                else:
                    self.logger.info("Puck OK.")
                    if robot_pusher == VerifyPresenceQuery.NOT_PRESENT:
                        self.logger.info("Robot pusher not found.")
                    else:
                        self.logger.info("Robot pusher OK.")
                        return self.SUCCESS

                i += 1
                if i >= self.tries:
                    break

        return self.FAIL
