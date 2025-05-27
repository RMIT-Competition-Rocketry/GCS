import logging
import cli.proccess as process
import platform
from typing import List, Optional
import time
import subprocess
import os


class PendantEmulatorSubprocess(process.LoggedSubProcess):
    """Subclass of LoggedSubProcess with a stop condition for callbacks.
    """

    def start(self):
        """
        OVERRIDE PARENT PROCESS ONLY TO AVOID PIPING AND THREADING BECAUSE THIS IS IN NEW WINDOW
        """
        self._process = subprocess.Popen(
            self._command,
            stdout=None,
            stderr=None,
            text=True,
            bufsize=1,
            env=self._env
        )
        self._logger_adapter.info(
            f"Started subprocess: {self._name} (PID: {self._process.pid})")

        # On macOS, get the PID of the terminal window thats opened
        if platform.system() == 'Darwin':
            self._external_terminal_pid = self._get_external_terminal_pid()

    def _get_external_terminal_pid(self) -> Optional[int]:
        """Get the PID of the terminal window opened by osascript."""
        START_TIME = time.monotonic()
        TIMEOUT_S = 2  # How long to wait for the external terminal to boot
        try:
            while time.monotonic() - START_TIME < TIMEOUT_S:
                result = subprocess.run(
                    ['pgrep', '-f', "\/backend\/pendant_emulator\.py -u"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self._logger_adapter.debug(
                        f"Found external PID: {result.stdout.strip()}")
                    return int(result.stdout.strip())
            self._logger_adapter.error("Failed to find external terminal PID")
        except Exception as e:
            self._logger_adapter.error(f"Failed to get terminal PID: {e}")
        return None

    def stop(self):
        """Stop the subprocess"""
        if self._process and self._process.returncode is None:
            self._process.terminate()
            self._process.wait()
            self._logger_adapter.info(
                f"Stopped subprocess: {self._name} (PID: {self._process.pid})"
            )
        if platform.system() == 'Darwin' and self._external_terminal_pid:
            try:
                kill_result = subprocess.run(
                    ['kill', str(self._external_terminal_pid)],
                    check=True,
                    capture_output=True,  # Capture both stdout and stderr
                    text=True  # Return output as string instead of bytes
                )
                self._logger_adapter.error(kill_result.stderr.strip())
                self._logger_adapter.error(kill_result.stdout.strip())
                self._logger_adapter.info(
                    f"Closed extra terminal window (PID: {self._external_terminal_pid})")
            except subprocess.CalledProcessError as e:
                self._logger_adapter.error(
                    f"Failed to close extra terminal window (PID: {self._external_terminal_pid}): {e}")
        try:
            self.__class__._instances.remove(self)
        except ValueError:
            self._logger_adapter.error(
                f"Failed to close my subprocess: {self._name} (PID:{self._process.pid})")


def get_command() -> List[str]:
    system = platform.system()
    project_root = os.path.abspath(os.getcwd())
    script_path = os.path.join(
        project_root, "backend", "pendant_emulator.py")

    if system == 'Darwin':
        # Use single quotes to handle spaces in paths
        shell_cmd = f"export PYTHONPATH='{project_root}'; python3 '{script_path}' -u"
        applescript = f'tell app "Terminal" to do script "{shell_cmd}"'
        return ['osascript', '-e', applescript]
    elif system == 'Linux':
        # Use xterm and explicitly pass DISPLAY
        display = os.environ.get('DISPLAY', ':0')
        shell_cmd = (
            f"export PYTHONPATH='{project_root}'; "
            f"export DISPLAY='{display}'; "
            f"python3 '{script_path}' -u; "
            "exec bash"
        )
        return ['xterm', '-e', 'bash', '-c', shell_cmd]
    else:
        raise NotImplementedError(f"Unsupported OS: {system}")


def start_pendant_emulator(logger: logging.Logger) -> None:
    SERVICE_NAME = "pendant_emulator"
    try:
        # Make sure to open it in a new terminal window.
        # Errors probably wont be shown if this is wrong
        PENDANT_EMULATOR_COMMAND = get_command()
        env = os.environ.copy()

        # Add project root for imports to work
        env["PYTHONPATH"] = os.path.abspath(os.getcwd())
        with open(os.path.join(os.path.sep, "tmp", "GCS_CONFIG_LOCATION.txt"), "w") as f:
            f.write(os.path.join(os.path.abspath(
                os.getcwd()), "config", "config.ini"))
        logger.debug(
            f"Starting {SERVICE_NAME} with: {PENDANT_EMULATOR_COMMAND}")
        pendant_process = PendantEmulatorSubprocess(
            PENDANT_EMULATOR_COMMAND,
            name=SERVICE_NAME,
            env=env)

        pendant_process.start()
        time.sleep(1)

    except Exception as e:
        logger.error(
            f"An error occurred while starting {SERVICE_NAME}: {e}")
        return None, None
