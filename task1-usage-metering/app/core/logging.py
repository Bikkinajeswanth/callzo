import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter for production observability.
    Emits timestamp, level, correlation_id, message, module, and extra fields.
    Never exposes credentials or secrets.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # Include correlation ID if present
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_record["correlation_id"] = record.correlation_id

        # Include additional structured data if provided
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            # Sanitize any sensitive key
            sanitized = {}
            for k, v in record.extra_data.items():
                if any(sec in k.lower() for sec in ["secret", "password", "token", "signature", "key"]):
                    sanitized[k] = "[REDACTED]"
                else:
                    sanitized[k] = v
            log_record["data"] = sanitized

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("callzo_metering")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = setup_logging()
