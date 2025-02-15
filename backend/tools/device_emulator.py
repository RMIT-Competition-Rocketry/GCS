from __future__ import absolute_import
from abc import ABC, abstractmethod
from backend import config
import logging
from typing import Optional, List
import sys
from backend.tools import metric
import datetime
import time

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
    _INITIALISED: bool = False  # Flag to check if the settings have been initialized

    @classmethod
    def initialize_settings(cls,
                            EMULATION_CONFIG: dict,
                            FAKE_DEVICE_NAME: str):
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
        cls._INITIALISED = True

    def __init__(self):
        if not self._INITIALISED:
            raise RuntimeError(
                "Cannot create instances of MockPacket or its subclasses before initializing class settings.")
        self.ID: Optional[int] = None  # Packet ID
        # High level payload builder
        self.payload_after_id: Optional[List[bytes]] = None

    def write_payload(self):
        """Writes payload of bytes to device"""

        try:
            with open(self._FAKE_DEVICE_NAME, 'wb') as device:
                device.write(metric.Metric._int_to_byte(self.ID))
                for byte in self.payload_after_id:
                    device.write(byte)
        except Exception as e:
            logger.error(
                f"Failed to write bytes to {self._FAKE_DEVICE_NAME}: {e}")
            raise


class GCStoAVStateCMD(MockPacket):
    def __init__(
        self,
        MAIN_SECONDARY_TEST: bool = False,
        MAIN_PRIMARY_TEST: bool = True,
        APOGEE_SECONDARY_TEST: bool = False,
        APROGEE_PRIMARY_TEST: bool = False,
        BEGIN_BROADCAST: bool = False,
    ):
        super().__init__()
        self.ID = 0x01
        self.payload_after_id = [
            metric.Metric.continuityCheckCMDFlags(
                MAIN_SECONDARY_TEST,
                MAIN_PRIMARY_TEST,
                APOGEE_SECONDARY_TEST,
                APROGEE_PRIMARY_TEST,
            ),
            metric.Metric.continuityCheckCMDFlagsINVERTED(
                MAIN_SECONDARY_TEST,
                MAIN_PRIMARY_TEST,
                APOGEE_SECONDARY_TEST,
                APROGEE_PRIMARY_TEST,
            ),
            metric.Metric.BroadcastBeginCMDFlags(BEGIN_BROADCAST)
        ]


class AVtoGCSData1(MockPacket):
    def __init__(
        self,
        FLIGHT_STATE_MSB=False,
        FLIGHT_STATE_1=False,
        FLIGHT_STATE_LSB=False,
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG=False,
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY=False,
        GPS_FIX_FLAG=False,
        PAYLOAD_CONNECTION_FLAG=True,
        CAMERA_CONTROLLER_CONNECTION=True,
        ACCEL_LOW_X=12345,
        ACCEL_LOW_Y=12345,
        ACCEL_LOW_Z=12345,
        ACCEL_HIGH_X=12345,
        ACCEL_HIGH_Y=12345,
        ACCEL_HIGH_Z=12345,
        GYRO_X=12345,
        GYRO_Y=12345,
        GYRO_Z=12345,
        ALTITUDE=1234567,
        VELOCITY=1234567,
        APOGEE_PRIMARY_TEST_COMPETE=True,
        APOGEE_SECONDARY_TEST_COMPETE=False,
        APOGEE_PRIMARY_TEST_RESULTS=False,
        APOGEE_SECONDARY_TEST_RESULTS=False,
        MAIN_PRIMARY_TEST_COMPETE=True,
        MAIN_SECONDARY_TEST_COMPETE=False,
        MAIN_PRIMARY_TEST_RESULTS=False,
        MAIN_SECONDARY_TEST_RESULTS=False,
        MOVE_TO_BROADCAST=False
    ):
        super().    __init__()
        self.ID = 0x03
        self.payload_after_id = [
            metric.Metric.StateFlags3p0(
                FLIGHT_STATE_MSB,
                FLIGHT_STATE_1,
                FLIGHT_STATE_LSB,
                DUAL_BOARD_CONNECTIVITY_STATE_FLAG,
                RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY,
                GPS_FIX_FLAG,
                PAYLOAD_CONNECTION_FLAG,
                CAMERA_CONTROLLER_CONNECTION,
            ),
            metric.Metric.ACCEL_LOW_X(ACCEL_LOW_X),
            metric.Metric.ACCEL_LOW_Y(ACCEL_LOW_Y),
            metric.Metric.ACCEL_LOW_Z(ACCEL_LOW_Z),
            metric.Metric.ACCEL_HIGH_X(ACCEL_HIGH_X),
            metric.Metric.ACCEL_HIGH_Y(ACCEL_HIGH_Y),
            metric.Metric.ACCEL_HIGH_Z(ACCEL_HIGH_Z),
            metric.Metric.GYRO_X(GYRO_X),
            metric.Metric.GYRO_Y(GYRO_Y),
            metric.Metric.GYRO_Z(GYRO_Z),
            metric.Metric.ALTITUDE(ALTITUDE),
            metric.Metric.VELOCITY(VELOCITY),
            metric.Metric.continuityCheckResultsApogee(
                APOGEE_PRIMARY_TEST_COMPETE,
                APOGEE_SECONDARY_TEST_COMPETE,
                APOGEE_PRIMARY_TEST_RESULTS,
                APOGEE_SECONDARY_TEST_RESULTS,
            ),
            metric.Metric.continuityCheckResultsMain(
                MAIN_PRIMARY_TEST_COMPETE,
                MAIN_SECONDARY_TEST_COMPETE,
                MAIN_PRIMARY_TEST_RESULTS,
                MAIN_SECONDARY_TEST_RESULTS,
            ),
            metric.Metric.MovingToBroadCastFlag(MOVE_TO_BROADCAST),
        ]


def main():
    logger.debug("Emulator starting")

    try:
        FAKE_DEVICE_NAME = sys.argv[sys.argv.index('--device-rocket') + 1]
    except ValueError:
        logger.error("Failed to find device names in arguments for emulator")
        raise

    MockPacket.initialize_settings(
        config.load_config()['emulation'],
        FAKE_DEVICE_NAME=FAKE_DEVICE_NAME,
    )

    # Also, this is the ROCKET emulator.
    # Packets written to the device should be packets that are sent from AV
    test_packet = AVtoGCSData1()

    START = datetime.datetime.now()
    while (datetime.datetime.now() - START).seconds < 60*10:  # 10 minute debug session
        test_packet.write_payload()
        time.sleep(1)

    logger.debug("Emulator finished")


if __name__ == '__main__':
    main()
