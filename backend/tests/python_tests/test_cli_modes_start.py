import subprocess
import sys
import os
from typing import List, Tuple, Generator
import time
import threading
import queue
import pytest
from abc import abstractmethod, ABC
import re


class ProcessOutputScanner:
    """Handles scanning process output for success/failure patterns."""

    def __init__(self, output_queue: queue.Queue):
        self.output_queue = output_queue
        self.captured_lines = []

    def scan_for_patterns(self, fail_any: List[str], success_all: List[str],
                          timeout: float = 10.0) -> Tuple[bool, List[str]]:
        """
        Scans output for failure/success patterns using regex.

        Args:
            fail_any: List of regex patterns - if any match, test fails
            success_all: List of regex patterns - all must match to succeed  
            timeout: How long to wait for patterns

        Returns:
            Tuple of (success: bool, captured_lines: List[str])
        """
        start_time = time.time()
        success_targets = set(success_all)

        # Compile regex patterns for better performance
        fail_regexes = [re.compile(pattern) for pattern in fail_any]
        success_regexes = {pattern: re.compile(
            pattern) for pattern in success_all}

        while time.time() - start_time < timeout:
            try:
                line = self.output_queue.get(timeout=0.1)
                self.captured_lines.append(line)
                print(line)  # debugging / action logs. Prints on fail only

                for fail_regex in fail_regexes:
                    if fail_regex.search(line):
                        print("Failure pattern matched:", line)
                        return False, self.captured_lines

                for success_pattern in list(success_targets):
                    if success_regexes[success_pattern].search(line):
                        success_targets.remove(success_pattern)

                if len(success_targets) == 0:
                    return True, self.captured_lines

            except queue.Empty:
                continue

        print("Remaining success patterns:", success_targets)
        return len(success_targets) == 0, self.captured_lines


class CliStartup(ABC):
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../.."))
    DEFAULT_FAIL_PATTERNS = [r"\[STDERR\](?!.*(?:This is a development server|Running on|Press CTRL\+C to quit)).*",
                             r"Traceback \(most recent call last\)",]
    DEFAULT_SUCCESS_PATTERNS = ["Starting development mode",
                                "socat: Stopping socat callbacks",  # found devices
                                r"middleware_server: \[STDOUT] Starting middleware server",
                                r"middleware_server: \[STDOUT] Interface initialised for type: TEST",
                                r"event viewer: \[STDOUT] Listening for messages\.\.\.",
                                "WebSocket server started at"]

    # Protected
    def _start_process(self, ROCKET_ARGS: list):
        if ROCKET_ARGS is None:
            raise NotImplementedError(
                "ROCKET_ARGS must be provided for your test class")

        cmd = [sys.executable, "-u", "rocket.py"]
        cmd.extend(ROCKET_ARGS)

        if "--nobuild" not in cmd:
            print(f"ROCKET_ARGS: {ROCKET_ARGS}")
            raise ValueError(
                "ROCKET_ARGS must include --nobuild for your test class")

        CLI_FILE_PATH = os.path.join(CliStartup.PROJECT_ROOT, 'rocket.py')
        print(f"Expected rocket.py path: {CLI_FILE_PATH}")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            cwd=CliStartup.PROJECT_ROOT
        )

        assert proc.pid and proc.pid > 0

        output_queue = queue.Queue()

        def _monitor_stream(stream, q):
            for line in iter(stream.readline, ''):
                q.put(line.strip())
            stream.close()

        thread = threading.Thread(target=_monitor_stream, args=(
            proc.stdout, output_queue), daemon=True)
        thread.start()

        # Send test the process and the output queue after fixture setup
        scanner = ProcessOutputScanner(output_queue)
        yield proc, scanner

        # Automatic cleanup (if test didn't already kill it)
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        thread.join(timeout=1)

    @pytest.fixture(scope="class")
    def process_and_scanner(self, request):
        """Call `_start_process` with appropriate args and return the process and scanner"""
        rocket_args = self.get_rocket_args()
        gen = self._start_process(rocket_args)
        proc, scanner = next(gen)
        yield proc, scanner
        try:
            next(gen)
        except StopIteration:
            pass

    @abstractmethod
    def get_rocket_args(self) -> List[str]:
        """Return the rocket.py arguments for this test class."""
        pass


@pytest.mark.skipif(os.getenv("CI_BUILD_ENV") != "Debug", reason="CI_BUILD_ENV undefined or not Debug")
class TestDevStartups(CliStartup):
    def get_rocket_args(self) -> List[str]:
        return ["dev", "--interface", "test", "--nopendant", "--nobuild"]

    def test_runs_successfully(self, process_and_scanner: Tuple[subprocess.Popen, ProcessOutputScanner]):
        proc, scanner = process_and_scanner
        fail_patterns = CliStartup.DEFAULT_FAIL_PATTERNS
        success_patterns = CliStartup.DEFAULT_SUCCESS_PATTERNS + [
            r"device emulator: \[STDOUT] Emulator starting",
        ]
        success, output_lines = scanner.scan_for_patterns(
            fail_any=fail_patterns,
            success_all=success_patterns,
            timeout=30.0
        )
        assert success, f"System failed to match patterns"
        print(f"System ran successfully. Captured {len(output_lines)} lines")


@pytest.mark.skipif(os.getenv("CI_BUILD_ENV") != "Debug", reason="CI_BUILD_ENV undefined or not Debug")
class TestReplaySimulationStartups(CliStartup):
    def get_rocket_args(self) -> List[str]:
        return ["replay", "--mode", "simulation", "--simulation", "test", "--nobuild"]

    def test_runs_successfully(self, process_and_scanner: Tuple[subprocess.Popen, ProcessOutputScanner]):
        proc, scanner = process_and_scanner
        fail_patterns = CliStartup.DEFAULT_FAIL_PATTERNS
        success_patterns = CliStartup.DEFAULT_SUCCESS_PATTERNS + [
            r"replay system: \[STDOUT] Starting simulation replay for TEST",
            r"event viewer: \[STDOUT] Flight state changed to COAST"
        ]
        success, output_lines = scanner.scan_for_patterns(
            fail_any=fail_patterns,
            success_all=success_patterns,
            timeout=30.0
        )
        assert success, f"System failed to match patterns"
        print(f"System ran successfully. Captured {len(output_lines)} lines")


@pytest.mark.skipif(os.getenv("CI_BUILD_ENV") != "Debug", reason="CI_BUILD_ENV undefined or not Debug")
class TestReplayMissionStartups(CliStartup):
    def get_rocket_args(self) -> List[str]:
        return ["replay", "--mode", "mission", "--mission", "20250504", "--nobuild"]

    def test_runs_successfully(self, process_and_scanner: Tuple[subprocess.Popen, ProcessOutputScanner]):
        proc, scanner = process_and_scanner
        fail_patterns = CliStartup.DEFAULT_FAIL_PATTERNS
        success_patterns = CliStartup.DEFAULT_SUCCESS_PATTERNS + [
            "Starting mission replay for 20250504",
        ]
        success, output_lines = scanner.scan_for_patterns(
            fail_any=fail_patterns,
            success_all=success_patterns,
            timeout=30.0
        )
        assert success, f"System failed to match patterns"
        print(f"System ran successfully. Captured {len(output_lines)} lines")
