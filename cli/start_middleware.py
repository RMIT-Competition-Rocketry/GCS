import logging
import cli.proccess as process
import os
import enum


class InterfaceType(enum.Enum):
    # Reference the main middleware cpp file
    UART = "UART"
    TEST = "TEST"


def start_middleware(logger: logging.Logger,
                     release: bool,
                     INTERFACE_TYPE: InterfaceType,
                     DEVICE_PATH: str,
                     SOCKET_PATH: str,
                     ):

    if not isinstance(INTERFACE_TYPE, InterfaceType):
        raise ValueError(
            f"INTERFACE_TYPE must be a InterfaceType value, got: {INTERFACE_TYPE} as type {type(INTERFACE_TYPE)}")
    try:

        BINARY = "middleware-release" if release else "middleware"

        MIDDLEWARE_COMMAND = [
            # Should always be relative to cwd. Just use the (.):
            # ./middleware/build/middleware {args}
            os.path.join(".", "build", BINARY),
            # <interface type> <device path> <socket path>
            INTERFACE_TYPE.value,
            DEVICE_PATH,
            SOCKET_PATH
        ]

        logger.debug(f"Starting middleware with: {MIDDLEWARE_COMMAND}")

        middleware_process = process.LoggedSubProcess(
            MIDDLEWARE_COMMAND,
            name="middleware",
            parse_output=True
        )
        middleware_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting middleware: {e}")
        # This is important, propogate this one
        raise
