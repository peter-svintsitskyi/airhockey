import logging
from airhockey.vision.query import QueryContext, VerifyPositionQuery
from airhockey.vision.color import ColorRange
from airhockey.utils import Timeout


class DetectTableHandler(object):
    FAIL = "FAIL"
    SUCCESS = "SUCCESS"

    def __init__(self, *,
                 expected_markers: list,
                 color_range: ColorRange,
                 vision_query_context: QueryContext,
                 tries: int,
                 delay: int
                 ):
        self.expected_markers = expected_markers
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.color_range = color_range
        self.vision_query_context = vision_query_context
        self.tries = tries
        self.delay = delay

    def __call__(self):
        i = 0
        t = Timeout(self.delay)
        while True:
            with self.vision_query_context as context:
                result = context.query(VerifyPositionQuery(
                    self.color_range,
                    self.expected_markers))

                if not t.timeout():
                    continue

                i += 1
                if i > self.tries:
                    break

                self.logger.info("Detecting table...")
                if result == VerifyPositionQuery.SUCCESS:
                    self.logger.info("Table markers detected.")
                    return self.SUCCESS
                elif result == VerifyPositionQuery.OUT_OF_POSITION:
                    self.logger.info("Table markers are out of position.")
                elif result == VerifyPositionQuery.NOT_DETECTED:
                    self.logger.info("Could not see table markers.")
                else:
                    raise RuntimeError(
                        "Query result {result} is not supported".format(
                            result=result))

        return self.FAIL
