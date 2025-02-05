import logging
import subprocess
from typing import List, Optional
import threading
import atexit
import sys  # Added to detect debugger

logger = logging.getLogger('rocket')


class LoggedSubProcess:
    """Object to manage subproccess called by this CLI with centralised logging"""
    _instances = []
    _auto_cleanup = True  # Flag to control cleanup behavior

    def __init__(self, command: List[str], name: Optional[str] = None, env: Optional[dict] = None):
        self.logger = logging.getLogger('rocket')
        self.command = command
        self.name = name or " ".join(command)
        self.process = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.env = env
        self.logger_adapter = logging.LoggerAdapter(
            self.logger,
            extra={"subprocess_name": self.name}
        )
        self.__class__._instances.append(self)

    def start(self):
        """Start the subprocess and monitor its output asynchronously"""
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=self.env
        )
        self.logger_adapter.info(
            f"Started subprocess: {self.name} (PID: {self.process.pid})")
        self.stdout_thread = threading.Thread(
            target=self._monitor_stream,
            args=(self.process.stdout, "STDOUT"),
            name=f"{self.name}_STDOUT")
        self.stderr_thread = threading.Thread(
            target=self._monitor_stream,
            args=(self.process.stderr, "STDERR"),
            name=f"{self.name}_STDERR")
        self.stdout_thread.daemon = True
        self.stderr_thread.daemon = True
        self.stdout_thread.start()
        self.stderr_thread.start()

    def stop(self):
        """Stop the subprocess"""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            self.process.wait()
            self.logger_adapter.info(
                f"Stopped subprocess: {self.name} (PID: {self.process.pid})"
            )
            self.stdout_thread.join()
            self.stderr_thread.join()
        try:
            self.__class__._instances.remove(self)
        except ValueError:
            self.logger_adapter.error(
                f"Failed to close my subprocess: {self.name} (PID:{self.process.pid})")

    def _monitor_stream(self, stream, stream_name):
        for line in iter(stream.readline, ''):
            if line.strip():  # Non empty lines
                if stream_name == "STDERR":
                    self.logger_adapter.error(
                        f"[{stream_name}] {line.strip()}")
                else:
                    self.logger_adapter.debug(
                        f"[{stream_name}] {line.strip()}")

    @classmethod
    def cleanup(cls):
        """Stop all instances unless debugger is active or auto_cleanup is False"""
        # Note to self that this applies to subclasses that don't override this method

        if not cls._auto_cleanup:
            return
        # Check if a debugger is active (e.g., pdb.set_trace())
        # if sys.gettrace() is not None:
        #     logger.debug(
        #         "Debugger detected: Skipping subprocess cleanup. Leaving all subprocess open")
        #     return
        for instance in list(cls._instances):
            instance.stop()


class ERRLoggedSubProcess(LoggedSubProcess):
    def _monitor_stream(self, stream, stream_name):
        for line in iter(stream.readline, ''):
            if line.strip():
                if stream_name == "STDERR":
                    self.logger_adapter.debug(
                        f"[{stream_name}] {line.strip()}")
                else:
                    self.logger_adapter.error(
                        f"[{stream_name}] {line.strip()}")
