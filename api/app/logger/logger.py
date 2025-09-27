import json
import logging
import logging.config
import sys
import time
from datetime import datetime, timezone

from flask import g, request


def get_logger(name):
    return logging.getLogger(name)


logger = get_logger(__name__)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add HTTP request fields if present
        http_fields = [
            "method",
            "path",
            "status_code",
            "duration_ms",
            "remote_addr",
            "user_agent",
        ]
        for field in http_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_config(level):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JSONFormatter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
                "level": level,
            }
        },
        "root": {"level": level, "handlers": ["console"]},
        "loggers": {
            "urllib3": {"level": "WARNING"},
            "requests": {"level": "WARNING"},
            "werkzeug": {"level": "WARNING"},
            "flask": {"level": "ERROR", "handlers": ["console"], "propagate": False},
        },
    }


def init(level):
    config = get_config(level)
    logging.config.dictConfig(config)


def start_request():
    g.start_time = time.time()


def log_request(response):
    duration = time.time() - g.start_time
    logger.info(
        "HTTP",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
        },
    )
    return response


def init_app(app):
    init(app.config["LOG_LEVEL"])
    app.logger = logging.getLogger("flask")

    app.before_request(start_request)
    app.after_request(log_request)
