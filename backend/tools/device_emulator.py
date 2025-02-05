from __future__ import absolute_import
from abc import ABC, abstractmethod
from configparser import ConfigParser
from backend import config
import logging


logger = logging.getLogger('rocket')


class MockPacket(ABC):
    DEVICE_NAME: str = None  # Name of the deivce in /dev/...
    _initialized: bool = False  # Flag to check if the settings have been initialized

    @classmethod
    def initialize_settings(cls, EMULATION_CONFIG: dict):
        """Initialise settings for the MockPacket object

        Args:
            EMULATION_CONFIG (dict): Config settings from an .ini file
        """

        if cls._initialized:
            raise ValueError("Settings have already been initialized.")
        if "emulator_device_name" not in EMULATION_CONFIG.keys():
            raise KeyError("Missing 'emulator_device_name' in configuration.")

        # Set static class values
        cls.DEVICE_NAME = EMULATION_CONFIG["emulator_device_name"]
        cls._initialized = True

    def __init__(self):
        if not self._initialized:
            raise RuntimeError(
                "Cannot create instances of MockPacket or its subclasses before initializing settings.")

    def write_bytes(self, byte_list):
        """Writes a list of bytes to the device stream

        Args:
            byte_list (list): List of bytes to write to the device
        """
        if not isinstance(byte_list, list) or not all(isinstance(b, int) and 0 <= b <= 255 for b in byte_list):
            raise ValueError(
                "byte_list must be a list of bytes (integers between 0 and 255).")

        try:
            with open(self.DEVICE_NAME, 'wb') as device:
                device.write(bytearray(byte_list))
        except Exception as e:
            logger.error(f"Failed to write bytes to {self.DEVICE_NAME}: {e}")
            raise


class DummyPacket(MockPacket):
    pass


def main():
    logger.debug("Emulator starting")
    MockPacket.initialize_settings(config.load_config()['emulation'])


if __name__ == '__main__':
    logger.info("Running device emulator")
    main()
