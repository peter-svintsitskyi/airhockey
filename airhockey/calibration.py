import logging
import time
from airhockey.vision.query import QueryContext, VerifyPositionQuery
from airhockey.vision.color import ColorRange


class CalibrateHandler(object):
    FAIL = "FAIL"
    SUCCESS = "SUCCESS"

    def __init__(self, *,
                 expected_markers: list,
                 log: str,
                 color_range: ColorRange,
                 vision_query_context: QueryContext,
                 tries: int,
                 delay: int
                 ):
        self.expected_markers = expected_markers
        self.logger = logging.getLogger(log)
        self.logger.setLevel(logging.INFO)
        self.color_range = color_range
        self.vision_query_context = vision_query_context
        self.tries = tries
        self.delay = delay

    def __call__(self):
        t1 = time.time()
        i = 0
        self.logger.info("Detecting table...")
        while True:
            with self.vision_query_context as context:
                result = context.query(VerifyPositionQuery(self.color_range, self.expected_markers))

                t2 = time.time()
                if t2 - t1 < 1:
                    continue
                t1 = time.time()
                i += 1
                if i >= self.tries - 1:
                    break

                if result == VerifyPositionQuery.SUCCESS:
                    self.logger.info("Table markers detected.")
                    return self.SUCCESS
                elif result == VerifyPositionQuery.OUT_OF_POSITION:
                    self.logger.info("Table markers are out of position.")
                elif result == VerifyPositionQuery.NOT_DETECTED:
                    self.logger.info("Could not see table markers.")
                else:
                    raise RuntimeError("Query result {result} is not supported".format(result=result))

        return self.FAIL

