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

        # Set PYTHONPATH to the project root to ensure imports work correctly.
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(
            os.path.join(os.path.dirname(__file__), ".."))

        emulator_process = process.LoggedSubProcess(
            SIMULATOR_COMMAND,
            name=SERVICE_NAME,
            parse_output=True,
            env=env,
        )
        emulator_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting {SERVICE_NAME}: {e}")
        return None, None
