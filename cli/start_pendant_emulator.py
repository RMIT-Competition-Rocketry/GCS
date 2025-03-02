import logging
import cli.proccess as process
import platform
from typing import List
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

    def stop(self):
        """Stop the subprocess"""
        if self._process and self._process.returncode is None:
            self._process.terminate()
            self._process.wait()
            self._logger_adapter.info(
                f"Stopped subprocess: {self._name} (PID: {self._process.pid})"
            )
        try:
            self.__class__._instances.remove(self)
        except ValueError:
            self._logger_adapter.error(
                f"Failed to close my subprocess: {self._name} (PID:{self._process.pid})")


def get_command() -> List[str]:
    system = platform.system()
    project_root = os.path.abspath(os.getcwd())
    script_path = os.path.join(
        project_root, "backend", "tools", "pendant_emulator.py")

    if system == 'Darwin':
        # Use single quotes to handle spaces in paths
        shell_cmd = f"export PYTHONPATH='{project_root}'; python3 '{script_path}' -u"
        applescript = f'tell app "Terminal" to do script "{shell_cmd}"'
        return ['osascript', '-e', applescript]
    elif system == 'Linux':
        # Keep terminal open after execution with 'exec bash'
        shell_cmd = f"export PYTHONPATH='{project_root}'; python3 '{script_path}' -u; exec bash"
        return ['gnome-terminal', '--', 'bash', '-c', shell_cmd]
    else:
        raise NotImplementedError(f"Unsupported OS: {system}")


def start_pendant_emulator(logger: logging.Logger) -> None:
    try:
        # Make sure to open it in a new terminal window.
        # Errors probably wont be shown if this is wrong
        PENDANT_EMULATOR_COMMAND = get_command()
        env = os.environ.copy()

        # Add project root for imports to work
        env["PYTHONPATH"] = os.path.abspath(os.getcwd())
        logger.debug(
            f"Starting pendant emulator with: {PENDANT_EMULATOR_COMMAND}")
        pendant_process = PendantEmulatorSubprocess(
            PENDANT_EMULATOR_COMMAND,
            name="pendant_emulator",
            env=env)

        pendant_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting a Socat fake serial device: {e}")
        return None, None
