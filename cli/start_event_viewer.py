import logging
import cli.proccess as process
from typing import Tuple
import os


class EventViewerSubprocess(process.LoggedSubProcess):
    """Subclass of LoggedSubProcess with a stop condition for callbacks.
    """

    def _update_callback_condition(self) -> bool:
        if self._callback_hits >= 1:
            self._logger_adapter.debug(
                "Stopping build callbacks for this process")
            return True
        return False


def successful_event_viewer_start_callback(line: str, stream_name: str):
    """Check if the event viewer has started successfully"""

    if "Listening for messages..." in line:
        return True


def start_event_viewer(logger: logging.Logger, SOCKET_PATH: str, file_logging_enabled: bool):
    SERVICE_NAME = "event viewer"
    try:

        EVENT_VIEWER_COMMAND = [
            "python3", "backend/event_viewer.py", "-u", "--socket-path", SOCKET_PATH
        ]

        if file_logging_enabled:
            EVENT_VIEWER_COMMAND.append("--no-log")

        logger.debug(f"Starting {SERVICE_NAME} with: {EVENT_VIEWER_COMMAND}")

        # Set PYTHONPATH to the project root to ensure imports work correctly.
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(
            os.path.join(os.path.dirname(__file__), ".."))

        event_viewer_process = EventViewerSubprocess(
            EVENT_VIEWER_COMMAND,
            name=SERVICE_NAME,
            env=env,
            parse_output=True
        )

        event_viewer_process.register_callback(
            successful_event_viewer_start_callback)

        event_viewer_process.start()

        finished = False
        while not finished:
            finished = event_viewer_process.get_parsed_data()

        logger.info(f"{SERVICE_NAME} started successfully")

    except Exception as e:
        logger.error(
            f"An error occurred while starting {SERVICE_NAME}: {e}")
        return None, None
