import logging
import cli.proccess as process


def start_frontend_api(logger: logging.Logger, SUB_SOCKET_PATH: str):
    SERVICE_NAME = "frontend_api"
    try:

        API_SERVICE_COMMAND = [
            "backend/frontend_api.py", "--socket-path", SUB_SOCKET_PATH
        ]

        logger.debug(
            f"Starting {SERVICE_NAME} module with: {API_SERVICE_COMMAND}")

        emulator_process = process.LoggedSubProcess(
            API_SERVICE_COMMAND,
            name="frontend_api",
            parse_output=True
        )
        emulator_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting the rocket frontend api: {e}")
        return None, None
