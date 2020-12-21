import logging
import time

from airhockey.utils import Timeout


class AwaitVideoHandler(object):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"

    def __init__(self, video_stream, timeout):
        self.video_stream = video_stream
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def __call__(self, *args, **kwargs):
        self.logger.info("Waiting for video stream...")
        t = Timeout(self.timeout)
        self.video_stream.start()
        while not self.video_stream.has_frame():
            if t.timeout():
                self.logger.info("Video stream timeout.")
                return self.TIMEOUT
            time.sleep(0.1)

        self.logger.info("Video stream OK.")
        return self.SUCCESS
