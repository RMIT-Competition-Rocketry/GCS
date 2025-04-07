import logging
import cli.proccess as process
import os
import enum
from typing import Optional


class InterfaceType(enum.Enum):
    # Reference the main middleware cpp file
    UART = "UART"
    TEST = "TEST"


def get_middleware_path(BINARY_NAME: str) -> Optional[str]:
    """Check if middleware is in build/ then check if it is in root folder.
    This helps when sharing releases, but still prioritises the build/ folder.
    """
    build_path = os.path.join(".", "build", BINARY_NAME)
    root_path = os.path.join(".", BINARY_NAME)

    if os.path.exists(build_path):
        return build_path
    elif os.path.exists(root_path):
        return root_path
    else:
        return None


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

        BINARY_NAME = "middleware_server_release" if release else "middleware_server"
        MIDDLEWARE_BINARY_PATH = get_middleware_path(BINARY_NAME)

        if MIDDLEWARE_BINARY_PATH is None:
            raise FileNotFoundError(
                f"Could not find middleware binary ({BINARY_NAME}) in build/ or root folder. Please run $ bash scripts/release.sh")

        MIDDLEWARE_COMMAND = [
            # Should always be relative to cwd. Just use the (.):
            # ./middleware/build/middleware_server {args}
            MIDDLEWARE_BINARY_PATH,
            # <interface type> <device path> <socket path>
            INTERFACE_TYPE.value,
            DEVICE_PATH,
            SOCKET_PATH
        ]

        logger.debug(f"Starting middleware with: {MIDDLEWARE_COMMAND}")

        middleware_process = process.LoggedSubProcess(
            MIDDLEWARE_COMMAND,
            name="middleware_server",
            parse_output=True
        )
        middleware_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting middleware: {e}")
        # This is important, propogate this one
        raise
