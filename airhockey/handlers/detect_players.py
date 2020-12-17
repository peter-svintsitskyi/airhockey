import logging

from airhockey.vision.query import VerifyPresenceQuery


class DetectPlayersHandler(object):
    FAIL = "FAIL"
    SUCCESS = "SUCCESS"

    def __init__(self, *, vision_query_context, puck_color_range, robot_pusher_color_range, tries):
        self.vision_query_context = vision_query_context
        self.puck_color_range = puck_color_range
        self.robot_pusher_color_range = robot_pusher_color_range
        self.tries = tries
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def __call__(self, *args, **kwargs):
        i = 0
        while True:
            with self.vision_query_context:
                i += 1
                if i > self.tries:
                    break

                self.logger.info("Detecting a puck and a robot pusher...")
                puck = self.vision_query_context.query(VerifyPresenceQuery(self.puck_color_range))
                if puck == VerifyPresenceQuery.NOT_PRESENT:
                    self.logger.info("Puck not found.")

                else:
                    self.logger.info("Puck OK.")
                    robot_pusher = self.vision_query_context.query(VerifyPresenceQuery(self.robot_pusher_color_range))
                    if robot_pusher == VerifyPresenceQuery.NOT_PRESENT:
                        self.logger.info("Robot pusher not found.")
                    else:
                        self.logger.info("Robot pusher OK.")
                        return self.SUCCESS

        return self.FAIL


