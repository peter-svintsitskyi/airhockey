import logging

from airhockey.vision.color import ColorRange
from airhockey.vision.query import QueryContext, PositionQuery


class PlayGameHandler:
    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'

    def __init__(
            self,
            *,
            vision_query_context: QueryContext,
            puck_color_range: ColorRange,
            pusher_color_range: ColorRange
    ):
        self.vision_query_context = vision_query_context
        self.puck_color_range = puck_color_range
        self.pusher_color_range = pusher_color_range
        self.logger = logging.getLogger(__name__)

    def __call__(self, *args, **kwargs):
        """
        [X] 1. See puck position
        2. Calculate puck velocity
        3. Calculate puck trajectory
        4. See pusher position
        5. Move pusher to the interception point
        """
        self.logger.info("Starting game")

        while True:
            with self.vision_query_context as context:
                puck_position = context.query(
                    PositionQuery(color_range=self.puck_color_range)
                )
                self.logger.info(f"puck position: {puck_position}")

                pusher_position = context.query(
                    PositionQuery(color_range=self.pusher_color_range)
                )
                self.logger.info(f"pusher position: {pusher_position}")





        return self.FAIL
