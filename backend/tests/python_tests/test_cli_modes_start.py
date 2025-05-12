import subprocess
import sys
import os
import signal
import time
import threading
import queue


# NOTE PLEASE READ DEV NOTES FOR UPGRADES
# --------------------
# Just whipped this up out of procrastination. Got a few ideas on how to make this better
# For a whole entire CLI system test like this, make a test fixure than can reuse the cli process
# Make some developer friendly methods to load in success and failure lines that can be read during operation from the reader thread
# Make sure to run with nobuild because it would already be there from the CMAKE test build
# Try and do black box tests for corrupt packets as just running the binary and not the CLI. Test the CLI at least once though
# Also maybe add a couple more lines to check for from each individual service in case one of them fails.
# --------------------

def test_cli_dev():
    print(sys.executable)
    cmd = [sys.executable, "-u", "rocket.py",
           "dev", "--interface", "test", "--nopendant", "--nobuild"]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
    print(
        f"Expected rocket.py path: {os.path.join(project_root, 'rocket.py')}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
        cwd=project_root
    )

    assert proc.pid and proc.pid > 0

    q = queue.Queue()

    def reader():
        for line in proc.stdout:
            q.put(line)
        q.put(None)

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    found_ws = False
    found_ev = False
    error_found = False
    lines = []
    start = time.monotonic()
    timeout = 10
    event_reading = False

    try:
        while time.monotonic() - start < timeout:
            try:
                line = q.get(timeout=timeout - (time.monotonic() - start))
            except queue.Empty:
                break
            if line is None:
                break
            lines.append(line)
            print(line, end='')
            if "WebSocket server started" in line:
                found_ws = True
            if "event viewer started successfully" in line:
                found_ev = True
            if "Supersonic flight detected" in line:
                event_reading = True
            if "Traceback (most recent call last)" in line:
                error_found = True
                # Close in 1 second
                timeout = time.monotonic() - start + 1
            if found_ws and found_ev and event_reading:
                proc.send_signal(signal.SIGINT)
                proc.wait(timeout=5)
                break
    finally:
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    output = "".join(lines)
    assert not error_found, f"Error found in output:\n{output}"
    assert found_ws, f"WebSocket server did not start. Output:\n{output}"
    assert found_ev, f"Event viewer did not start. Output:\n{output}"
    assert event_reading, f"Event reading probably did not start. Output:\n{output}"
