import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for structured backend logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "trace_id",
            "module_name",
            "event",
            "error_code",
            "duration_ms",
            "fallback",
            "model_id",
            "temperature",
            "max_tokens",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
