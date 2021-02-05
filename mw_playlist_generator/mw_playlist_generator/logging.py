"""
everything to do with logging

other modules only import the log attribute
"""
import logging
import logging.config
from logging import Logger

__all__ = ["log", "Logger"]

LEVELS = {
    "FATAL": 50,
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "WARN": 30,
    "INFO": 20,
    "DEBUG": 10,
}

LOGGING_CONFIG = {
    "version": 1,
    "incremental": False,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "[%(levelname)s] %(message)s",
        },
        "debug_formatter": {
            "format": "%(asctime)s,%(msecs)d %(name)s %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "debug_console": {
            "class": "logging.StreamHandler",
            "formatter": "debug_formatter",
            "level": "DEBUG",
            "stream": "ext://sys.stderr",
        },
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["debug_console"],
    },
}


def setup_logging(name: str = __name__, level: str = "INFO") -> Logger:
    "configure basic logging"
    # Finding level names:
    # import logging
    # from functools import partial
    # lvalue = partial(getattr, logging)
    # levels = [
    #     level
    #     for level in dir(logging)
    #     if level.isupper() and level.isalpha() and lvalue(level) > 0
    # ]
    # {k: v for v, k in reversed(sorted(zip(map(lvalue, levels), levels)))}
    if level.upper() not in LEVELS:
        raise ValueError(f"'{level}' is not one of [{', '.join(LEVELS.keys())}]")

    logging.config.dictConfig(LOGGING_CONFIG)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


log = setup_logging(name="generator")
