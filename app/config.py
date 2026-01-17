import logging
from logging.config import dictConfig


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    COLORS = {
        "DEBUG": "\033[37m",  # Gray
        "INFO": "\033[34m",  # Blue
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord):
        log_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def configure_logging():
    """Configure application logging with colored output"""
    dictConfig(
        {
            "version": 1,
            "filters": {
                "info_and_warning": {
                    "()": lambda: type(
                        "",
                        (object,),
                        {
                            "filter": lambda self, record: record.levelno
                            < 40  # < ERROR (40)
                        },
                    )(),
                },
                "error_and_critical": {
                    "()": lambda: type(
                        "",
                        (object,),
                        {
                            "filter": lambda self, record: record.levelno
                            >= 40  # >= ERROR (40)
                        },
                    )(),
                },
            },
            "formatters": {
                "colored": {
                    "()": ColoredFormatter,
                    "format": "[%(asctime)s.%(msecs)03d] [%(levelname)-8s] [%(name)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "colored",
                    "filters": ["info_and_warning"],
                },
                "stderr": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                    "formatter": "colored",
                    "filters": ["error_and_critical"],
                },
            },
            "root": {"level": "INFO", "handlers": ["stdout", "stderr"]},
        }
    )
