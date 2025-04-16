import logging
import cli.proccess as process
import os


def start_simulator(logger: logging.Logger, DEVICE: str):
    SERVICE_NAME = "simulator"
    try:

        SIMULATOR_COMMAND = [
            "python3", "-u", os.path.join("backend",
                                          "simulation", "run_simulation.py"),
            "--device-rocket", DEVICE
        ]

        logger.debug(
            f"Starting {SERVICE_NAME} module with: {SIMULATOR_COMMAND}")

        emulator_process = process.LoggedSubProcess(
            SIMULATOR_COMMAND,
            name=SERVICE_NAME,
            parse_output=True
        )
        emulator_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting {SERVICE_NAME}: {e}")
        return None, None
