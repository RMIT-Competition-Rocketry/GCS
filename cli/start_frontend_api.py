import logging
import cli.proccess as process
import os


def start_frontend_api(logger: logging.Logger, SUB_SOCKET_PATH: str):
    SERVICE_NAME = "frontend_api"
    try:

        API_SERVICE_COMMAND = [
            "python3", os.path.join(
                "backend", "frontend_api.py"), "--socket-path", SUB_SOCKET_PATH
        ]

        logger.debug(
            f"Starting {SERVICE_NAME} module with: {API_SERVICE_COMMAND}")

        # Set PYTHONPATH to the project root to ensure imports work correctly.
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(
            os.path.join(os.path.dirname(__file__), ".."))

        api_process = process.LoggedSubProcess(
            API_SERVICE_COMMAND,
            name=SERVICE_NAME,
            env=env,
            parse_output=True
        )
        api_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting the rocket {SERVICE_NAME} {e}")
        return None, None
