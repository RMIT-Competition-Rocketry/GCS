import logging
import cli.proccess as process
from typing import Tuple


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
    try:

        EVENT_VIEWER_COMMAND = [
            "python3", "backend/event_viewer.py", "-u", "--socket-path", SOCKET_PATH
        ]

        if file_logging_enabled:
            EVENT_VIEWER_COMMAND.append("--no-log")

        logger.debug(f"Starting event viewer with: {EVENT_VIEWER_COMMAND}")

        event_viewer_process = EventViewerSubprocess(
            EVENT_VIEWER_COMMAND,
            name="event_viewer",
        )

        event_viewer_process.register_callback(
            successful_event_viewer_start_callback)

        event_viewer_process.start()

        finished = False
        while not finished:
            finished = event_viewer_process.get_parsed_data()

        logger.info("Event viewer started successfully")

    except Exception as e:
        logger.error(
            f"An error occurred while starting the rocket AV emulator: {e}")
        return None, None
