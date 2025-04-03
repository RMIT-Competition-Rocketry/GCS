import logging
from config.config import load_config

# log level (between INFO (20) and WARNING (30))
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")


class CustomFormatter(logging.Formatter):
    """Logging formatter from https://stackoverflow.com/a/56944256/14141223"""

    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    GREEN = "\x1b[32;20m"           # New color for SUCCESS
    RESET = "\x1b[0m"
    # Maybe add %(asctime)s later if needed
    FORMAT = "[%(levelname)-7s] %(filename)s.%(subprocess_name)s: %(message)s"

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
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def create_handler() -> logging.StreamHandler:
    """Create console handler with a highest log level"""
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(CustomFormatter())
    return ch


def initialise():
    """One time logging setup run as soon as the program starts"""

    logger = logging.getLogger("rocket")
    if logger.hasHandlers():
        # Clear existing handlers to avoid duplicates
        logger.warning(
            "Logger has been initialised before. Stop intialising it again please")
        logger.handlers.clear()

    LOG_LEVEL = load_config()['logging']['level'].upper().strip()
    LOG_MAPPING = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'SUCCESS': SUCCESS_LEVEL_NUM,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    LOG_LEVEL_OBJECT = LOG_MAPPING.get(LOG_LEVEL, logging.INFO)
    logger.setLevel(LOG_LEVEL_OBJECT)
    logger.addHandler(create_handler())
    return logger


def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)


logging.Logger.success = success


def adapter_success(self, message, *args, **kwargs):
    self.logger.success(message, *args, **kwargs)


logging.LoggerAdapter.success = adapter_success
