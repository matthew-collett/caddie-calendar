import json
import logging
import logging.config
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
        )


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


def init_app(app):
    init(app.config["LOG_LEVEL"])
    app.logger = logging.getLogger("flask")


logger = logging.getLogger("app")
