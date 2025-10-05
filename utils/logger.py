from logging import getLogger, INFO, StreamHandler, Formatter
from sys import stdout
from inspect import currentframe


class GWWLogger:
    def __init__(
        self,
        name=None,
        level=INFO,
        colored_output=True,
    ):
        self.logger = getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            console_handler = StreamHandler(stdout)
            console_handler.setLevel(level)

            if colored_output:
                formatter = ColoredFormatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%d/%m/%y - %H:%M:%S",
                )
            else:
                formatter = Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%d/%m/%y - %H:%M:%S",
                )

            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _get_caller_info(self):
        frame = currentframe().f_back.f_back
        return f"[{frame.f_code.co_filename}:{frame.f_lineno}]"

    def debug(self, message, **kwargs):
        self.logger.debug(f"{self._get_caller_info()} {message}", **kwargs)

    def info(self, message, **kwargs):
        self.logger.info(f"{self._get_caller_info()} {message}", **kwargs)

    def warning(self, message, **kwargs):
        self.logger.warning(f"{self._get_caller_info()} {message}", **kwargs)

    def error(self, message, exc_info=False, **kwargs):
        self.logger.error(
            f"{self._get_caller_info()} {message}", exc_info=exc_info, **kwargs
        )

    def critical(self, message, **kwargs):
        self.logger.critical(f"{self._get_caller_info()} {message}", **kwargs)

    def exception(self, message, **kwargs):
        self.logger.exception(f"{self._get_caller_info()} {message}", **kwargs)


class ColoredFormatter(Formatter):
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)
