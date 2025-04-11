import logging
import cli.proccess as process
from enum import Enum
import os


class CMakeBuildModes(Enum):
    DEBUG = "Debug"
    RELEASE = "Release"


class MiddlewareBuildSubprocess(process.LoggedSubProcess):
    """Subclass of LoggedSubProcess with a stop condition for callbacks.
    """

    def _update_callback_condition(self) -> bool:
        if self._callback_hits >= 1:
            self._logger_adapter.debug(
                "Stopping build callbacks for this process")
            return True
        return False


def successful_cmake_build_callback(line: str, stream_name: str):
    """Check if the cmake build worked"""

    if "-- Build files have been written to:" in line:
        return True


def successful_make_build_callback(line: str, stream_name: str):
    """Check if the make build worked"""

    if "[100%] Built target" in line:
        return True


def start_middleware_build(logger: logging.Logger, BUILD_FLAG: CMakeBuildModes):
    if not isinstance(BUILD_FLAG, CMakeBuildModes):
        raise ValueError(
            f"BUILD_FLAG must be a CMakeBuildModes value, got: {BUILD_FLAG} as type {type(BUILD_FLAG)}")
    try:
        build_flag_string = BUILD_FLAG.value

        os.makedirs("build", exist_ok=True)
        os.chdir("build")
        MIDDLEWARE_BUILD_COMMAND_CMAKE = [
            "cmake", f"-DCMAKE_BUILD_TYPE={build_flag_string}", ".."]

        logger.debug(
            f"Starting middleware build [cmake] with: {MIDDLEWARE_BUILD_COMMAND_CMAKE}")

        middleware_build_process_cmake = MiddlewareBuildSubprocess(
            MIDDLEWARE_BUILD_COMMAND_CMAKE,
            name="middleware-build-cmake",
        )
        middleware_build_process_cmake.register_callback(
            successful_cmake_build_callback)
        middleware_build_process_cmake.start()

        finished = False
        while not finished:
            finished = middleware_build_process_cmake.get_parsed_data()

        logger.info("CMake build finished")

        # ---- Start make ----

        MIDDLEWARE_BUILD_COMMAND_MAKE = [
            "make"
        ]

        logger.debug(
            f"Starting middleware build [make] with: {MIDDLEWARE_BUILD_COMMAND_MAKE}")

        middleware_build_process_make = MiddlewareBuildSubprocess(
            MIDDLEWARE_BUILD_COMMAND_MAKE,
            name="middleware-build-make",
        )

        middleware_build_process_make.register_callback(
            successful_make_build_callback)
        middleware_build_process_make.start()

        finished = False
        while not finished:
            finished = middleware_build_process_make.get_parsed_data()

        os.chdir("..")  # Back out of build dir
        logger.info("Make build finished")

    except Exception as e:
        logger.error(
            f"An error occurred while building middleware: {e}")
        # Propogate to a blocking handler in cli
        raise
        # return None, None
