import logging
import cli.proccess as process
import cli.start_middleware as start_middleware


def start_fake_serial_device_emulator(logger: logging.Logger, DEVICE: str,
                                      INTERFACE_TYPE: start_middleware.InterfaceType,
                                      experimental: bool) -> None:
    SERVICE_NAME = "device emulator"
    try:

        EMULATOR_COMMAND = [
            "python3", "-u", "-Xfrozen_modules=off", "-m", "backend.device_emulator",
            "--device-rocket", DEVICE, "--interface-type", INTERFACE_TYPE.value, "--experimental"
        ]

        logger.debug(
            f"Starting {SERVICE_NAME} module with: {EMULATOR_COMMAND} with interface type: {INTERFACE_TYPE}")

        emulator_process = process.LoggedSubProcess(
            EMULATOR_COMMAND,
            name=SERVICE_NAME,
            parse_output=True
        )
        emulator_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting {SERVICE_NAME}: {e}")
        raise
