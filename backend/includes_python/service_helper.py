import signal
import backend.includes_python.process_logging as slogger

# IMPORT THIS FILE IN YOUR MAIN SERVICE FILE
# This adds signals handlers to gracefully shut down the service
# import me and use if service_helper.time_to_stop() where you need
# .
# import backend.includes_python.service_helper as service_helper
# .

# Please use this for Git issue #120

# This global variable will be set to False on SIGINT
running = True

SIGNAL_MAP = {
    signal.SIGINT: "Keyboard Interrupt (SIGINT)",
    signal.SIGTERM: "Termination Request (SIGTERM)",
    signal.SIGHUP: "Terminal Hangup (SIGHUP)",
    signal.SIGQUIT: "Quit Signal (SIGQUIT)",
}


def time_to_stop():
    """
    Returns True if the service should stop running.
    """
    return not running


def _handle_signal(signum, frame):
    if signum in SIGNAL_MAP:
        stop_reason = SIGNAL_MAP[signum]
    else:
        stop_reason = f"Recieved unhandled signal: {signum}"

    global running
    slogger.info(f"{stop_reason} — shutting down service.")
    running = False


# Register the handler when this module is imported
signal.signal(signal.SIGINT, _handle_signal)
