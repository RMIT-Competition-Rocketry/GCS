from __future__ import absolute_import
from abc import ABC, abstractmethod
from backend import config
import logging
from typing import Optional
import sys

logger = logging.getLogger('rocket')

# If you're running directly, this will create a logger for you for testing purposes
if not logger.hasHandlers():

    handler = logging.StreamHandler()
    # This logger is regurgitated by the upstream rocket cli logger. So it can be minimal
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    # logger.warning(
    #     "Created manual logger for device emulator for testing purposes")


class MockPacket(ABC):
    # Name of the fake device socat has made
    _FAKE_DEVICE_NAME: Optional[str] = None
    # Name of the fake device socat has made for monitoring
    _FAKE_DEVICE_NAME_MONITOR: Optional[str] = None
    _INITIALISED: bool = False  # Flag to check if the settings have been initialized

    @classmethod
    def initialize_settings(cls,
                            EMULATION_CONFIG: dict,
                            FAKE_DEVICE_NAME: str,
                            FAKE_DEVICE_NAME_MONITOR: str):
        """Initialise settings for the MockPacket object

        Args:
            EMULATION_CONFIG (dict): Config settings from an .ini file
        """

        if cls._INITIALISED:
            raise ValueError("Settings have already been initialized.")
        # Might need this config code later, if it's like march or later it can go
        # if "emulator_device_name" not in EMULATION_CONFIG.keys():
        #     raise KeyError("Missing 'emulator_device_name' in configuration.")

        # Set static class values
        cls._FAKE_DEVICE_NAME = FAKE_DEVICE_NAME
        cls._FAKE_DEVICE_NAME_MONITOR = FAKE_DEVICE_NAME_MONITOR
        cls._INITIALISED = True

    def __init__(self):
        if not self._INITIALISED:
            raise RuntimeError(
                "Cannot create instances of MockPacket or its subclasses before initializing class settings.")

    def write_bytes(self, data_bytes: bytes):
        """Writes a list of bytes to the device stream"""
        if not isinstance(data_bytes, bytes):
            raise ValueError(
                "data_bytes must be bytes")

        try:
            with open(self._FAKE_DEVICE_NAME, 'wb') as device:
                device.write(data_bytes)
        except Exception as e:
            logger.error(
                f"Failed to write bytes to {self._FAKE_DEVICE_NAME}: {e}")
            raise


class DummyPacket(MockPacket):
    pass


def main():
    logger.debug("Emulator starting")

    try:
        FAKE_DEVICE_NAME = sys.argv[sys.argv.index('--device-rocket') + 1]
        FAKE_DEVICE_NAME_MONITOR = \
            sys.argv[sys.argv.index('--device-monitor') + 1]
    except ValueError:
        logger.error("Failed to find device names in arguments for emulator")
        raise

    MockPacket.initialize_settings(
        config.load_config()['emulation'],
        FAKE_DEVICE_NAME=FAKE_DEVICE_NAME,
        FAKE_DEVICE_NAME_MONITOR=FAKE_DEVICE_NAME_MONITOR
    )

    test_packet = DummyPacket()
    test_packet.write_bytes(b"Hello, world!")

    logger.debug("Emulator finished")


if __name__ == '__main__':
    main()
