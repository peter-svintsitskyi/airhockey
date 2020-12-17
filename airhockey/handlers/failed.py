import logging


class FailedHandler(object):
    def __call__(self, *args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        logger.info("Failed. Terminating...")