import logging
import re
import cli.proccess as process
from typing import Tuple


class SocatSubprocess(process.ERRLoggedSubProcess):
    """Subclass of the ERRLoggedSubProcess with a stop condition for callbacks.
    """

    def _update_callback_condition(self) -> bool:
        if self._callback_hits >= 2:
            # We only need to read 2 devices from the terminal output. 2 hits is enough
            self._logger_adapter.debug("Stopping socat callbacks")
            return True
        return False


def device_name_callback(line: str, stream_name: str):
    """Get the device name/path generated from socat"""

    # Example output from socat.
    # 2025/02/06 20:53:44 socat[56067] N PTY is /dev/ttys012
    # 2025/02/06 20:53:44 socat[56067] N PTY is /dev/ttys016

    # $ echo "Hello Serial" > /dev/ttys012
    # $ echo "Hello Serial" > /dev/ttys012

    # 2025/02/06 21:08:47 socat[56254] N write(7, 0x126814000, 13) completed
    # 2025/02/06 21:08:53 socat[56254] N write(7, 0x126814000, 13) completed

    # Please note that both fake serial devices are linked,
    #   but when you read from one the buffer is cleared
    # That means that you use one as the 'fake device' and the other can just be
    #   for montitoring because nothing will steal the bytes going to it from
    #   the other linked device

    # TODO extract the device names and pass them back to the CLI handler.
    # Then probably start coding the emulator and protobuf?

    if "N PTY is" in line:
        REGEX_PATTERN = r"N PTY is (.+)"
        match = re.search(REGEX_PATTERN, line)
        if match is None:
            raise RuntimeError("Socat output parsing failed to find device")
        return match.group(1)


def start_fake_serial_device(logger: logging.Logger) -> Tuple[str, str]:
    """
    Starts a fake serial device using socat and logs the output.
    Returns a tuple containing the paths of the two generated pseudo-terminals.

    Will wait until fake serial termincal have started to return
    """
    try:

        SOCAT_COMMAND = ["socat", "-d", "-d",
                         "pty,raw,echo=0", "pty,raw,echo=0"]
        logger.debug(f"Starting socat with: {SOCAT_COMMAND}")
        socat_proccess = SocatSubprocess(SOCAT_COMMAND, name="socat")
        socat_proccess.start()

        socat_proccess.register_callback(device_name_callback)
        devices = []
        while len(devices) < 2:
            devices += socat_proccess.get_parsed_data()

        logger.debug(f"Devices found: {devices}")

    except Exception as e:
        logger.error(
            f"An error occurred while starting a Socat fake serial device: {e}")
        return None, None
