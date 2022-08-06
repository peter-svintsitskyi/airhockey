import logging

from airhockey.vision.query import Query, QueryContext


class LogHandlerSpy(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def handle(self, record: logging.LogRecord) -> bool:
        self.messages.append(record.msg)
        return True


def init_spy_log_handler(name):
    log_handler = LogHandlerSpy()
    log_handler.setLevel(logging.INFO)
    logger = logging.getLogger(name)
    logger.addHandler(log_handler)
    return log_handler


class QueryContextMock(QueryContext):
    def __init__(self):
        self.query_results = None
        self.call_count = None
        self.executed_queries = None
        self.context_enter_count = None
        self.can_execute = False

    def mock_query_results(self, query_results: list):
        self.query_results = query_results
        self.call_count = 0
        self.executed_queries = []
        self.context_enter_count = 0

    def query(self, query: Query) -> str:
        if not self.can_execute:
            raise RuntimeError(
                'Cannot execute a query from inactive context')

        call_count = self.call_count
        self.call_count += 1
        self.executed_queries.append(query)
        return self.query_results[call_count]

    def __enter__(self):
        self.can_execute = True
        self.context_enter_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.can_execute = False
        pass
