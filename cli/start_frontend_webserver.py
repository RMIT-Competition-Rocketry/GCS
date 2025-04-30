import logging
import cli.proccess as process


def start_frontend_webserver(logger: logging.Logger):
    SERVICE_NAME = "frontend_webserver"
    try:

        # TODO:
        # - Add port and debug configuration
        # - Proper logging

        FRONTEND_COMMAND = [
            "flask", "--app", "frontend.flask_server", "--debug", "run",
        ]

        logger.debug(
            f"Starting {SERVICE_NAME} module with: {FRONTEND_COMMAND}")

        frontend_process = process.LoggedSubProcess(
            FRONTEND_COMMAND,
            name=SERVICE_NAME,
            parse_output=True
        )
        frontend_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting {SERVICE_NAME}: {e}")
        return None, None
