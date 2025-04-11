import logging
import cli.proccess as process
import os
import enum
from typing import Optional


class InterfaceType(enum.Enum):
    # Reference the main middleware cpp file
    UART = "UART"
    TEST = "TEST"


def get_middleware_path(BINARY_NAME_PREFIX: str) -> Optional[str]:
    """Check if middleware is in build/ then check if it is in root folder.
    This helps when sharing releases, but still prioritises the build/ folder.
    """

    # Cmake folder
    BUILD_PATH_ABS = os.path.join(os.getcwd(), "build", "build")
    build_path_files = [os.path.join(BUILD_PATH_ABS, x)
                        for x in os.listdir(BUILD_PATH_ABS)]
    build_path_files = [x for x in build_path_files if os.path.isfile(x)]
    # User placed
    PROJECT_PATH_ABS = os.getcwd()
    project_root_files = [os.path.join(BUILD_PATH_ABS, x)
                          for x in os.listdir(PROJECT_PATH_ABS)]
    project_root_files = [x for x in project_root_files if os.path.isfile(x)]

    file_matches = []
    for path in build_path_files + project_root_files:
        filename = os.path.basename(path)
        if filename.startswith(BINARY_NAME_PREFIX):
            file_matches.append(path)

    if len(file_matches) > 1:
        raise RuntimeError(
            f"Multiple middleware binaries found. Please remove or archive the extra ones: {file_matches}")
    elif len(file_matches) == 0:
        return None

    return file_matches[0]


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

        BINARY_NAME = "middleware_release" if release else "middleware_debug"
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
