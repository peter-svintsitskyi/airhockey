import logging


class SpyLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def handle(self, record: logging.LogRecord) -> None:
        self.messages.append(record.msg)
        pass


def init_spy_log_handler(name):
    log_handler = SpyLogHandler()
    log_handler.setLevel(logging.INFO)
    logger = logging.getLogger(name)
    logger.addHandler(log_handler)
    return log_handler
