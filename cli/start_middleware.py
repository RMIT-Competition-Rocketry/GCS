import logging
import cli.proccess as process
import os
import enum
import config.config as config
from typing import Optional


class InterfaceType(enum.Enum):
    # Reference the main middleware cpp file
    UART = "UART"
    TEST = "TEST"
    TEST_UART = "TEST_UART"


def get_interface_type(interface: Optional[str]) -> InterfaceType:
    """Get the interface type from the command line argument or config"""
    if interface is None:  # Unspecified by user
        interface = config.load_config(
        )['hardware']['interface'].strip().upper()
    else:
        interface = interface.strip().upper()

    # Convert string to InterfaceType enum
    try:
        for enum_member in InterfaceType:
            if enum_member.name == interface:
                return enum_member
        # If we get here, no matching enum value was found
        valid_types = [e.name for e in InterfaceType]
        raise ValueError(
            f"Invalid interface type: '{interface}'. Valid types are: {', '.join(valid_types)}")
    except Exception as e:
        raise ValueError(f"Invalid interface type: {interface}")


class MiddlewareSubprocess(process.LoggedSubProcess):
    """Subclass of LoggedSubProcess with a stop condition for callbacks.
    """

    def _update_callback_condition(self) -> bool:
        if self._callback_hits >= 1:
            self._logger_adapter.debug(
                "Stopping build callbacks for this process")
            return True
        return False


def middleware_started_callback(line: str, stream_name: str):
    """Check if middleware has started"""

    if "Middleware server started successfully" in line:
        return True


def get_middleware_path(BINARY_NAME_PREFIX: str) -> Optional[str]:
    """Check if middleware is in build/ then check if it is in root folder.
    This helps when sharing releases, but still prioritises the build/ folder.
    """

    # Cmake folder
    BUILD_PATH_ABS = os.path.join(os.getcwd(), "build")
    build_path_files = [os.path.join(BUILD_PATH_ABS, x)
                        for x in os.listdir(BUILD_PATH_ABS)]
    build_path_files = [x for x in build_path_files if os.path.isfile(x)]
    # User placed
    PROJECT_PATH_ABS = os.getcwd()
    project_root_files = [os.path.join(PROJECT_PATH_ABS, x)
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

    BINARY_PATH = file_matches[0]

    with open("VERSION", "r") as f:
        version = f.read().strip()

    # Actual file may have build metadata in it. Substring match is fine
    if version not in os.path.basename(BINARY_PATH):
        raise RuntimeError(
            f"Middleware binary version mismatch. Expected substring: {version}, found: {os.path.basename(BINARY_PATH)}. The repository branch VERSION file does not match the binary version found")

    return file_matches[0]


def start_middleware(logger: logging.Logger,
                     release: bool,
                     INTERFACE_TYPE: InterfaceType,
                     DEVICE_PATH: str,
                     SOCKET_PATH: str,
                     opt_arg: Optional[str] = None,
                     ):

    if not isinstance(INTERFACE_TYPE, InterfaceType):
        raise ValueError(
            f"INTERFACE_TYPE must be a InterfaceType value, got: {INTERFACE_TYPE} as type {type(INTERFACE_TYPE)}")
    SERVICE_NAME = "middleware_server"
    try:

        BINARY_NAME = "middleware_release" if release else "middleware_debug"
        MIDDLEWARE_BINARY_PATH = get_middleware_path(BINARY_NAME)

        if MIDDLEWARE_BINARY_PATH is None:
            logger.debug(f"WORKING DIRECTORY: {os.getcwd()}")
            raise FileNotFoundError(
                f"Could not find {SERVICE_NAME} binary ({BINARY_NAME}) in build/ or root folder. Please run $ bash scripts/release.sh")

        middleware_command = [
            # Should always be relative to cwd. Just use the (.):
            # ./middleware/build/middleware_server {args}
            MIDDLEWARE_BINARY_PATH,
            # <interface type> <device path> <socket path>
            INTERFACE_TYPE.value,
            DEVICE_PATH,
            SOCKET_PATH,
        ]

        if opt_arg is not None:
            middleware_command.append(opt_arg)

        logger.debug(f"Starting {SERVICE_NAME} with: {middleware_command}")

        middleware_process = MiddlewareSubprocess(
            middleware_command,
            name=SERVICE_NAME,
            parse_output=True
        )
        middleware_process.register_callback(middleware_started_callback)
        middleware_process.start()
        finished = False
        while not finished:
            finished = middleware_process.get_parsed_data()

    except Exception as e:
        logger.error(
            f"An error occurred while starting {SERVICE_NAME}: {e}")
        # This is important, propogate this one
        raise
