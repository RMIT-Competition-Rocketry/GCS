import logging
import cli.proccess as process
from config.config import load_config


# TODO: Implement logging

class IgnoreWebMessagesFilter(logging.Filter):
    """Filter to exclude unneeded web messages"""

    def filter(self, record: logging.LogRecord) -> bool:
        return "GET" not in record.getMessage()


def start_frontend_webserver(logger: logging.Logger, debug: bool = False):
    SERVICE_NAME = "frontend_webserver"
    try:
        FRONTEND_COMMAND = [
            "flask",
            "--app",
            "frontend.flask_server",
            *(["--debug"] if debug else []),
            "run",
            "--host=0.0.0.0",
            f"--port={load_config()['frontend']['http_port'].strip()}"
        ]

        logger.debug(
            f"Starting {SERVICE_NAME} module with: {FRONTEND_COMMAND}")

        frontend_process = process.LoggedSubProcess(
            FRONTEND_COMMAND,
            name=SERVICE_NAME,
            parse_output=False
        )
        frontend_process._parent_logger.addFilter(IgnoreWebMessagesFilter())
        frontend_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting {SERVICE_NAME}: {e}")
        return None, None
