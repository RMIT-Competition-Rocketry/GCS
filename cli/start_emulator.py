import logging
import cli.proccess as process


def start_fake_serial_device_emulator(logger: logging.Logger, DEVICE: str):
    SERVICE_NAME = "device emulator"
    try:

        EMULATOR_COMMAND = [
            "python3", "-u", "-Xfrozen_modules=off", "-m", "backend.tools.device_emulator",
            "--device-rocket", DEVICE
        ]

        logger.debug(
            f"Starting {SERVICE_NAME} module with: {EMULATOR_COMMAND}")

        emulator_process = process.LoggedSubProcess(
            EMULATOR_COMMAND,
            name=SERVICE_NAME,
            parse_output=True
        )
        emulator_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting {SERVICE_NAME}: {e}")
        return None, None
