import logging
import cli.proccess as process
from typing import Tuple


def start_fake_serial_device_emulator(logger: logging.Logger, devices: Tuple[str, str]):
    try:

        EMULATOR_COMMAND = [
            "python3", "-u", "-Xfrozen_modules=off", "-m", "backend.tools.device_emulator",
            "--device-rocket", devices[0], "--device-monitor", devices[1]
        ]

        logger.debug(f"Starting emulator module with: {EMULATOR_COMMAND}")

        emulator_process = process.LoggedSubProcess(
            EMULATOR_COMMAND,
            name="emulator",
        )
        emulator_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting the rocket AV emulator: {e}")
        return None, None
