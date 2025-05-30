import logging
import re
import subprocess
from typing import List, Optional, Callable
import threading
from queue import Queue
import backend.includes_python.process_logging as slogger

logger = logging.getLogger('rocket')


class LoggedSubProcess:
    """Object to manage subproccess called by this CLI with centralised logging"""
    # All instances of this class.
    _instances = []
    # Flag to control cleanup behavior. True means it will cleanup automatically
    _auto_cleanup = True
    # How long to wait for the process to finish before killing it
    CLEANUP_TIMEOUT_S = 3

    def __init__(self,
                 command: List[str],
                 name: Optional[str] = None,
                 env: Optional[dict] = None,
                 parse_output: bool = False):
        """
        Args:
            command (List[str]): List of terminal arguments to run the subprocess
            name (Optional[str], optional): Name for the subprocess Defaults to None.
            env (Optional[dict], optional): Environment variables. Defaults to None.
            parse_output (bool): Parse output for logging levels? Defaults to False. Set this to true if you are using the slogger subprocess logging system.
        """
        self._parent_logger = logging.getLogger('rocket')
        if (any("python" in arg for arg in command) and not any("-u" in arg for arg in command)):
            self._parent_logger.warning(
                "Python subprocesses must have the `-u` flag to prevent buffering")
        self._command = command
        self._name = name or " ".join(command)
        self._process = None
        self._PARSE_OUTPUT = parse_output
        self._stdout_thread = None
        self._stderr_thread = None
        self._FLIP_STREAMS = False  # Flip STDERR and STDOUT
        self._env = env
        # Use logger_adaptor to log from this class
        self._logger_adapter = logging.LoggerAdapter(
            self._parent_logger,
            extra={"subprocess_name": self._name}
        )
        self._stop_callbacks: bool = False
        self._callback_data_available = threading.Event()
        self._callbacks = []
        self._callback_hits: int = 0  # Amount of callbacks that have returned values
        self._parsed_data = Queue()  # Thread-safe queue apparently
        self.__class__._instances.append(self)

    def register_callback(self, callback: Callable[[str, str], None]):
        """Register a callback to be called when a specific line is detected"""
        if self._process is not None:
            self._logger_adapter.warning(
                "You have added callbacks after process has started. Race conditions possible")
        self._logger_adapter.debug(
            f"Registering callback: {callback.__name__}")
        self._callbacks.append(callback)
        self._logger_adapter.debug(
            f"Registered  callback: {callback.__name__}")

    def start(self):
        """Start the subprocess and monitor its output asynchronously"""
        self._process = subprocess.Popen(
            self._command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=self._env,
            start_new_session=True  # For SIGINT handling with cleanup method
        )
        self._logger_adapter.info(
            f"Started subprocess: {self._name} (PID: {self._process.pid})")
        self._stdout_thread = threading.Thread(
            target=self._monitor_stream,
            args=(self._process.stdout, "STDOUT"),
            name=f"{self._name}_STDOUT")
        self._stderr_thread = threading.Thread(
            target=self._monitor_stream,
            args=(self._process.stderr, "STDERR"),
            name=f"{self._name}_STDERR")
        self._stdout_thread.daemon = True
        self._stderr_thread.daemon = True
        self._stdout_thread.start()
        self._stderr_thread.start()

    def stop(self):
        """Stop the subprocess"""
        if self._process and self._process.returncode is None:
            self._process.terminate()
            self._process.wait(LoggedSubProcess.CLEANUP_TIMEOUT_S)
            self._logger_adapter.info(
                f"Stopped subprocess: {self._name} (PID: {self._process.pid})"
            )
            self._stdout_thread.join()
            self._stderr_thread.join()
        try:
            self.__class__._instances.remove(self)
            # EXCEPTION TO A RULE OF THUMB HERE:
            # if (x._process is not None) in this debug is only to avoid raising
            # another error when cleaning up if a process object has been
            # instantiated but never started. It should not be needed if
            # everything starts fine
            INSTANCE_DEBUG_PID = [
                f'({x._name}: {x._process.pid})' for x in self.__class__._instances if x._process is not None]
            self._logger_adapter.debug(
                f"Remaining instances: {INSTANCE_DEBUG_PID}")
        except ValueError:
            self._logger_adapter.error(
                f"Failed to close my subprocess: {self._name} (PID:{self._process.pid})")

    def _update_callback_condition(self) -> bool:
        """Should callbacks stop? If this returns `False` callbacks will continue. `True` will permanently stop all callbacks.
        This will run after all callbacks are completed for each line.
        Please override this method in subclasses to change the behavior of the callback system.

        Default is to return False

        ---

        ### If you plan on running a finite amount of callbacks, override this method."""
        return False

    def _run_callbacks(self, stripped_line: str, stream_name: str) -> None:
        """Run callbacks in [`self.callbacks`]"""
        # Check for specific patterns or lines and invoke callbacks
        for callback in self._callbacks:
            callback_output = callback(stripped_line, stream_name)
            # Store parsed data in the queue
            if callback_output is not None:
                self._parsed_data.put(callback_output)
                self._callback_hits += 1
                self._callback_data_available.set()

    def _log_monitored_stream(self,
                              stripped_line: str,
                              stream_name: str,
                              level: Optional[str]) -> None:
        """When given a line and it's origin stream, log it with the appropriate level

        Args:
            stripped_line (str): A line of charcater output with no trailing whitespace
            stream_name (str): The stream name: STDERR or STDOUT for example
            level (str): The log level to use
        """

        def _format(stream, line):
            return f"[{stream}] {line}"  # ╰─▶ or ╰ or ╰─ ??

        # This is for things like SOCAT that just puts everything in STDERR
        if stream_name == "STDERR" and self._FLIP_STREAMS:
            stream_name = "MANUAL"

        match level:
            case None:
                # Were you intending to find a level?
                if self._PARSE_OUTPUT:
                    # Level was not found in the original message.
                    # Level should be able to be found with regex pattern specified in process_logging.py
                    self._logger_adapter.error(
                        _format(stream_name, f"LEVEL_UNDEF:{stripped_line}")
                    )
                else:
                    if stream_name == "STDERR":
                        self._logger_adapter.error(
                            _format(stream_name, stripped_line))
                    else:
                        self._logger_adapter.debug(
                            _format(stream_name, stripped_line)
                        )
            case "DEBUG":
                self._logger_adapter.debug(_format(stream_name, stripped_line))
            case "INFO":
                self._logger_adapter.info(_format(stream_name, stripped_line))
            case "SUCCESS":
                self._logger_adapter.success(
                    _format(stream_name, stripped_line))
            case "WARNING":
                self._logger_adapter.warning(
                    _format(stream_name, stripped_line))
            case "ERROR":
                self._logger_adapter.error(_format(stream_name, stripped_line))
            case "CRITICAL":
                self._logger_adapter.critical(
                    _format(stream_name, stripped_line))
            case _:
                # Level was found but not in an expected format
                self._logger_adapter.error(
                    _format(stream_name, f"LEVEL_WRONG:{stripped_line}")
                )

    def _monitor_stream(self, stream, stream_name):
        for line in iter(stream.readline, ''):
            line = line.strip()
            if line:  # Non-empty lines by 'truthy' check of blank string
                if self._PARSE_OUTPUT:
                    match = re.match(slogger.REGEX_MATCH, line)
                    level: Optional[str] = match.group(1) if match else None
                else:
                    level = None
                # remove level prefix
                line = re.sub(slogger.REGEX_MATCH, '', line)
                self._log_monitored_stream(line, stream_name, level)
                if self._stop_callbacks == False:
                    self._run_callbacks(line, stream_name)
                    self._stop_callbacks = self._update_callback_condition()

    def get_parsed_data(self):
        """Retrieve parsed data from the queue. This will empty the queue of course"""
        if self._process is None:
            raise RuntimeError(
                "Cannot get data for a process that has not started or has already stopped")
        self._callback_data_available.wait()  # Wait for the thread to set event
        data = []
        while not self._parsed_data.empty():
            data.append(self._parsed_data.get())
        self._callback_data_available.clear()  # Remove the threading event
        return data

    @classmethod
    def cleanup(cls):
        """Stop all instances unless debugger is active or auto_cleanup is False"""
        # Note to self that this applies to subclasses that don't override this method

        if not cls._auto_cleanup:
            return
        # Cleanup here must be done in the reverse order of creation.
        # Which it is for now
        # But race conditions can fuck this up. Like closing socat before the device emulator
        SHUTDOWN_ORDER = list(reversed(cls._instances))
        for instance in SHUTDOWN_ORDER:
            instance.stop()
            instance._process.wait(LoggedSubProcess.CLEANUP_TIMEOUT_S)


class ERRLoggedSubProcess(LoggedSubProcess):
    """Subclass of LoggedSubProcess that logs STDERR as DEBUG instead"""

    def __init__(self, command, name=None, env=None):
        super().__init__(command, name, env)
        self._FLIP_STREAMS = True
