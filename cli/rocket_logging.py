import logging
from config.config import load_config
import time
from typing import Optional
import os
import re

# Capture application start time (initialized in `initialise()`)
APP_START_TIME: Optional[float] = None

# log level (between INFO (20) and WARNING (30))
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

LOG_MAPPING = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'SUCCESS': SUCCESS_LEVEL_NUM,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


class CustomFormatter(logging.Formatter):
    """Logging formatter from https://stackoverflow.com/a/56944256/14141223"""

    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    GREEN = "\x1b[32;20m"
    RESET = "\x1b[0m"
    # Maybe add %(asctime)s later if needed
    FORMAT = "[%(levelname)-7s] %(post_start_s)5s s | %(subprocess_name)s: %(message)s"

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + RESET,
        logging.INFO: GREY + FORMAT + RESET,
        SUCCESS_LEVEL_NUM: GREEN + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET
    }

    def format(self, record):
        if not hasattr(record, "subprocess_name"):
            record.subprocess_name = ""  # Default empty value
        if APP_START_TIME is None:
            record.post_start_s = "0000.000"
        else:
            elapsed_s = (time.perf_counter() - APP_START_TIME)
            record.post_start_s = f"{elapsed_s:09.3f}"
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class PlainFormatter(CustomFormatter):
    """A formatter that strips ANSI control characters for clean log files"""

    def format(self, record):
        # First format with the parent formatter that adds colors
        formatted_message = super().format(record)
        # Strip ANSI escape sequences using regex
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', formatted_message)


def create_handler(LEVEL: int = logging.DEBUG) -> logging.StreamHandler:
    """Create console handler with specified level"""
    ch = logging.StreamHandler()
    ch.setLevel(LEVEL)
    ch.setFormatter(CustomFormatter())
    return ch


def create_file_handler(log_file_path: str) -> logging.FileHandler:
    """Create file handler to write logs to a file"""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    fh = logging.FileHandler(log_file_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(PlainFormatter())
    return fh


def initialise():
    """One time logging setup run as soon as the program starts"""

    global APP_START_TIME
    APP_START_TIME = time.perf_counter()

    logger = logging.getLogger("rocket")
    if logger.hasHandlers():
        # Clear existing handlers to avoid duplicates
        logger.warning(
            "Logger has been initialised before. Stop intialising it again please")
        logger.handlers.clear()

    config = load_config()
    LOG_LEVEL = config['logging']['level'].strip()

    # Get log file path from config or use default
    LOG_DIR_PATH = config['logging']['cli_log_dir'].strip()
    log_filename = f"cli_{time.strftime('%Y%m%d_%H%M%S')}.log"
    log_file_path = os.path.join(LOG_DIR_PATH, log_filename)

    LOG_LEVEL_OBJECT = LOG_MAPPING.get(LOG_LEVEL, logging.INFO)
    # Parent level is debug, capture everything
    logger.setLevel(logging.DEBUG)

    # Add both console and file handlers with different levels
    logger.addHandler(create_handler(LOG_LEVEL_OBJECT))
    logger.addHandler(create_file_handler(log_file_path))  # Always DEBUG

    # logger.info(f"Log file created at: {log_file_path}")
    return logger


def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)


logging.Logger.success = success


def adapter_success(self, message, *args, **kwargs):
    self.logger.success(message, *args, **kwargs)


logging.LoggerAdapter.success = adapter_success


def set_console_log_level(level_name: str):
    """
    Set the log level of the console handler at runtime.

    Args:
        level_name: Name of the log level (e.g., 'DEBUG', 'INFO', 'WARNING')
    """
    logger = logging.getLogger("rocket")

    # Convert level name to level number
    if level_name in LOG_MAPPING:
        level = LOG_MAPPING[level_name]
    else:
        logger.error(f"Invalid log level: {level_name}. Using INFO.")
        level = logging.INFO

    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(level)
            logger.debug(
                f"Console log level set to {level_name} post intialisation")
            return

    logger.warning("No console handler found")
