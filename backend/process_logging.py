
# This is for children processes that log independently of the CLI.

# The CLI will will pipe the logging output from subprocesses to the console.
# This file is just to enforce a consistent logging format across all processes
#   for correct CLI parsing

REGEX_MATCH = r"<(\w{4,8})>:"


def _log(MESSAGE: str, LEVEL: str):
    print(f"<{LEVEL}>:{MESSAGE}", flush=True)


def debug(MESSAGE: str):
    _log(MESSAGE, "DEBUG")


def info(MESSAGE: str):
    _log(MESSAGE, "INFO")


def success(MESSAGE: str):
    _log(MESSAGE, "SUCCESS")


def warning(MESSAGE: str):
    _log(MESSAGE, "WARNING")


def error(MESSAGE: str):
    _log(MESSAGE, "ERROR")


def critical(MESSAGE: str):
    _log(MESSAGE, "CRITICAL")
