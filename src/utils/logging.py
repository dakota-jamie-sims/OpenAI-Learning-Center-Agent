import os
import json
import logging as _logging
from typing import Optional


class _JsonFormatter(_logging.Formatter):
    """Format logs as JSON objects."""

    def format(self, record: _logging.LogRecord) -> str:
        log_record = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def get_logger(name: Optional[str] = None) -> _logging.Logger:
    """Return a configured logger.

    Log level is controlled by the ``LOG_LEVEL`` environment variable and the
    format by ``LOG_FORMAT`` (``plain`` or ``json``). Defaults to ``INFO`` level
    and plain text formatting.
    """
    logger = _logging.getLogger(name)
    if logger.handlers:
        return logger

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(_logging, level_name, _logging.INFO)
    logger.setLevel(level)

    handler = _logging.StreamHandler()
    log_format = os.getenv("LOG_FORMAT", "plain").lower()
    if log_format == "json":
        formatter = _JsonFormatter()
    else:
        formatter = _logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
