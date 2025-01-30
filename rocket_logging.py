import logging
from backend.config import load_config


class CustomFormatter(logging.Formatter):
    """Logging formatter from https://stackoverflow.com/a/56944256/14141223"""

    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"
    # Maybe add %(asctime)s later if needed
    FORMAT = "[%(levelname)s]\t %(filename)s.%(subprocess_name)s:\t %(message)s"

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + RESET,
        logging.INFO: GREY + FORMAT + RESET,
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
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    LOG_LEVEL_OBJECT = LOG_MAPPING.get(LOG_LEVEL, logging.INFO)

    logger.setLevel(LOG_LEVEL_OBJECT)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    ch.setFormatter(CustomFormatter())

    logger.addHandler(ch)
