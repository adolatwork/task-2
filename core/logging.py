import json
import logging

from contextvars import ContextVar
from pythonjsonlogger.jsonlogger import JsonFormatter


current_request: ContextVar[dict] = ContextVar("current_request", default={})


logger = logging.getLogger("json_logger")
logger.setLevel(logging.INFO)


class CustomJsonFormatter(JsonFormatter):
    def process_log_record(self, log_record):
        log_record.pop('taskName', None)
        return super().process_log_record(log_record)


json_formatter = CustomJsonFormatter(
    "%(asctime)s %(levelname)s %(message)s %(user)s %(method)s %(endpoint)s %(params)s %(body)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
plain_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class ConditionalFormatHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        user = getattr(record, "user", None)
        formatter = json_formatter
        if user is None or user == 'Anonymous':
            formatter = plain_formatter
        self.setFormatter(formatter)
        super().emit(record)


class CustomContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        request_info = current_request.get()
        record.method = request_info.get("method", "N/A")
        record.endpoint = request_info.get("endpoint", "N/A")
        record.params = json.dumps(request_info.get('params', {}))
        record.body = json.dumps(request_info.get('body', {}))
        return True


conditional_handler = ConditionalFormatHandler()
context_filter = CustomContextFilter()

logger.addHandler(conditional_handler)
logger.addFilter(context_filter)
