from __future__ import absolute_import
from abc import ABC, abstractmethod
from backend import config
from typing import Optional, List
import sys
from backend import metric
from backend import config
import os
import time
import backend.process_logging as slogger  # slog deez nuts

# TODO convert this crap into kwargs or something


class MockPacket(ABC):
    # Name of the fake device socat has made
    _FAKE_DEVICE_NAME: Optional[str] = None
    _INITIALISED: bool = False  # Flag to check if the settings have been initialized

    @classmethod
    def initialize_settings(cls,
                            EMULATION_CONFIG: dict,
                            FAKE_DEVICE_NAME: str = None):
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
        if self._FAKE_DEVICE_NAME is None:
            raise ValueError("Cannot write to device. Device name not set.")
        try:
            with open(self._FAKE_DEVICE_NAME, 'wb') as device:
                device.write(metric.Metric._int_to_byte_unsigned(self.ID))
                for byte in self.payload_after_id:
                    device.write(byte)
        except Exception as e:
            slogger.error(
                f"Failed to write bytes to {self._FAKE_DEVICE_NAME}: {e}")
            raise

    def get_payload_bytes(self) -> bytes:
        """Concatenates the ID and payload fragments into a single bytes object."""
        payload_bytes = bytearray()
        payload_bytes.extend(metric.Metric._int_to_byte_unsigned(self.ID))
        for fragment in self.payload_after_id:
            payload_bytes.extend(fragment)
        return bytes(payload_bytes)


class GCStoGSEStateCMD(MockPacket):
    def __init__(
        self,
        MANUAL_PURGE: bool = False,
        O2_FILL_ACTIVATE: bool = True,
        SELECTOR_SWITCH_NEUTRAL_POSITION: bool = False,
        N2O_FILL_ACTIVATE: bool = False,
        IGNITION_FIRE: bool = False,
        IGNITION_SELECTED: bool = False,
        GAS_FILL_SELECTED: bool = False,
        SYSTEM_ACTIVATE: bool = False,
    ):
        super().__init__()
        self.ID = 0x02
        self.payload_after_id = [
            metric.Metric.StateSetFlags2p1(MANUAL_PURGE,
                                           O2_FILL_ACTIVATE,
                                           SELECTOR_SWITCH_NEUTRAL_POSITION,
                                           N2O_FILL_ACTIVATE,
                                           IGNITION_FIRE,
                                           IGNITION_SELECTED,
                                           GAS_FILL_SELECTED,
                                           SYSTEM_ACTIVATE,),
            metric.Metric.StateSetFlagINVERTEDs2p2(MANUAL_PURGE,
                                                   O2_FILL_ACTIVATE,
                                                   SELECTOR_SWITCH_NEUTRAL_POSITION,
                                                   N2O_FILL_ACTIVATE,
                                                   IGNITION_FIRE,
                                                   IGNITION_SELECTED,
                                                   GAS_FILL_SELECTED,
                                                   SYSTEM_ACTIVATE,),
            metric.Metric.dummyByte()
        ]


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
        ACCEL_LOW_X=2048*1,
        ACCEL_LOW_Y=2048*2,
        ACCEL_LOW_Z=-2048*3,
        ACCEL_HIGH_X=-1024*1,
        ACCEL_HIGH_Y=-1024*2,
        ACCEL_HIGH_Z=1024*3,
        GYRO_X=int(1/0.00875),
        GYRO_Y=int(2/0.00875),
        GYRO_Z=int(3/0.00875),
        ALTITUDE=1234,
        VELOCITY=1234,
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
            # Note the dummy byte here for TBC purposes
            metric.Metric.dummyByte()
        ]


class AVtoGCSData2(MockPacket):
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
        LATITUDE="-37.80808500000",  # Must be 15 chars. Don't include null byte
        LONGITUDE="144.96507800000",
    ):
        super().__init__()
        self.ID = 0x04
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
            metric.Metric.GPS(LATITUDE, LONGITUDE)
        ]


class AVtoGCSData3(MockPacket):
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
    ):
        super().__init__()
        self.ID = 0x05
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
            # TBC for rest of the bytes?
        ] + [metric.Metric.dummyByte()]*30


class GSEtoGCSData1(MockPacket):
    def __init__(
        self,
        MANUAL_PURGED: bool = False,
        O2_FILL_ACTIVATED: bool = False,
        SELECTOR_SWITCH_NEUTRAL_POSITION: bool = False,
        N2O_FILL_ACTIVATED: bool = False,
        IGNITION_FIRED: bool = True,
        IGNITION_SELECTED: bool = False,
        GAS_FILL_SELECTED: bool = False,
        SYSTEM_ACTIVATED: bool = False,
        TRANSDUCER1: float = 1234,
        TRANSDUCER2: float = 1234,
        TRANSDUCER3: float = 1234,
        THERMOCOUPLE1: float = 1234,
        THERMOCOUPLE2: float = 1234,
        THERMOCOUPLE3: float = 1234,
        THERMOCOUPLE4: float = 1234,
        IGNITION_ERROR: bool = False,
        RELAY3_ERROR: bool = False,
        RELAY2_ERROR: bool = True,
        RELAY1_ERROR: bool = False,
        THERMOCOUPLE_4_ERROR: bool = False,
        THERMOCOUPLE_3_ERROR: bool = False,
        THERMOCOUPLE_2_ERROR: bool = True,
        THERMOCOUPLE_1_ERROR: bool = False,
        LOAD_CELL_4_ERROR: bool = False,
        LOAD_CELL_3_ERROR: bool = False,
        LOAD_CELL_2_ERROR: bool = False,
        LOAD_CELL_1_ERROR: bool = False,
        TRANSDUCER_4_ERROR: bool = False,
        TRANSDUCER_3_ERROR: bool = False,
        TRANSDUCER_2_ERROR: bool = False,
        TRANSDUCER_1_ERROR: bool = True,
    ):
        super().__init__()
        self.ID = 0x06
        self.payload_after_id = [
            metric.Metric.StateSetFlags2p1(
                MANUAL_PURGED,
                O2_FILL_ACTIVATED,
                SELECTOR_SWITCH_NEUTRAL_POSITION,
                N2O_FILL_ACTIVATED,
                IGNITION_FIRED,
                IGNITION_SELECTED,
                GAS_FILL_SELECTED,
                SYSTEM_ACTIVATED,
            ),
            metric.Metric.TRANSDUCER(TRANSDUCER1),
            metric.Metric.TRANSDUCER(TRANSDUCER2),
            metric.Metric.TRANSDUCER(TRANSDUCER3),
            metric.Metric.THERMOCOUPLE(THERMOCOUPLE1),
            metric.Metric.THERMOCOUPLE(THERMOCOUPLE2),
            metric.Metric.THERMOCOUPLE(THERMOCOUPLE3),
            metric.Metric.THERMOCOUPLE(THERMOCOUPLE4),
            metric.Metric.ERROR_CODE_GSE(
                IGNITION_ERROR,
                RELAY3_ERROR,
                RELAY2_ERROR,
                RELAY1_ERROR,
                THERMOCOUPLE_4_ERROR,
                THERMOCOUPLE_3_ERROR,
                THERMOCOUPLE_2_ERROR,
                THERMOCOUPLE_1_ERROR,
                LOAD_CELL_4_ERROR,
                LOAD_CELL_3_ERROR,
                LOAD_CELL_2_ERROR,
                LOAD_CELL_1_ERROR,
                TRANSDUCER_4_ERROR,
                TRANSDUCER_3_ERROR,
                TRANSDUCER_2_ERROR,
                TRANSDUCER_1_ERROR,
            )
        ]


class GSEtoGCSData2(MockPacket):
    def __init__(
        self,
        MANUAL_PURGED: bool = False,
        O2_FILL_ACTIVATED: bool = False,
        SELECTOR_SWITCH_NEUTRAL_POSITION: bool = False,
        N2O_FILL_ACTIVATED: bool = False,
        IGNITION_FIRED: bool = True,
        IGNITION_SELECTED: bool = False,
        GAS_FILL_SELECTED: bool = False,
        SYSTEM_ACTIVATED: bool = False,
        INTERNAL_TEMPERATURE: float = 30.123,
        WIND_SPEED: float = 20.123,
        GAS_BOTTLE_WEIGHT_1: int = 2,  # Error because alsmost empty
        GAS_BOTTLE_WEIGHT_2: int = 8,  # Impossible value for 6.5 ltr tank
        ADDITIONAL_VA_1: float = 5.123,
        ADDITIONAL_VA_2: float = 6.123,
        ADDITIONAL_CURRENT_1: float = 14.123,
        ADDITIONAL_CURRENT_2: float = 13.123,
        IGNITION_ERROR: bool = False,
        RELAY3_ERROR: bool = False,
        RELAY2_ERROR: bool = True,
        RELAY1_ERROR: bool = False,
        THERMOCOUPLE_4_ERROR: bool = False,
        THERMOCOUPLE_3_ERROR: bool = False,
        THERMOCOUPLE_2_ERROR: bool = True,
        THERMOCOUPLE_1_ERROR: bool = False,
        LOAD_CELL_4_ERROR: bool = False,
        LOAD_CELL_3_ERROR: bool = False,
        LOAD_CELL_2_ERROR: bool = False,
        LOAD_CELL_1_ERROR: bool = False,
        TRANSDUCER_4_ERROR: bool = False,
        TRANSDUCER_3_ERROR: bool = False,
        TRANSDUCER_2_ERROR: bool = False,
        TRANSDUCER_1_ERROR: bool = True,
    ):
        super().__init__()
        self.ID = 0x07
        self.payload_after_id = [
            metric.Metric.StateSetFlags2p1(
                MANUAL_PURGED,
                O2_FILL_ACTIVATED,
                SELECTOR_SWITCH_NEUTRAL_POSITION,
                N2O_FILL_ACTIVATED,
                IGNITION_FIRED,
                IGNITION_SELECTED,
                GAS_FILL_SELECTED,
                SYSTEM_ACTIVATED,
            ),
            metric.Metric.INTERNAL_TEMP_GSE(INTERNAL_TEMPERATURE),
            metric.Metric.WIND_SPEED_GSE(WIND_SPEED),
            metric.Metric.GAS_BOTTLE_WEIGHT(GAS_BOTTLE_WEIGHT_1),
            metric.Metric.GAS_BOTTLE_WEIGHT(GAS_BOTTLE_WEIGHT_2),
            metric.Metric.ADDITIONAL_VA_INPUT(ADDITIONAL_VA_1),
            metric.Metric.ADDITIONAL_VA_INPUT(ADDITIONAL_VA_2),
            metric.Metric.ADDITIONAL_CURRENT_INPUT(ADDITIONAL_CURRENT_1),
            metric.Metric.ADDITIONAL_CURRENT_INPUT(ADDITIONAL_CURRENT_2),
            metric.Metric.ERROR_CODE_GSE(
                IGNITION_ERROR,
                RELAY3_ERROR,
                RELAY2_ERROR,
                RELAY1_ERROR,
                THERMOCOUPLE_4_ERROR,
                THERMOCOUPLE_3_ERROR,
                THERMOCOUPLE_2_ERROR,
                THERMOCOUPLE_1_ERROR,
                LOAD_CELL_4_ERROR,
                LOAD_CELL_3_ERROR,
                LOAD_CELL_2_ERROR,
                LOAD_CELL_1_ERROR,
                TRANSDUCER_4_ERROR,
                TRANSDUCER_3_ERROR,
                TRANSDUCER_2_ERROR,
                TRANSDUCER_1_ERROR,
            )
        ]


def main():
    slogger.debug("Emulator starting")

    try:
        FAKE_DEVICE_NAME = sys.argv[sys.argv.index('--device-rocket') + 1]
    except ValueError:
        slogger.error("Failed to find device names in arguments for emulator")
        raise

    MockPacket.initialize_settings(
        config.load_config()['emulation'],
        FAKE_DEVICE_NAME=FAKE_DEVICE_NAME,
    )

    # Also, this is the ROCKET emulator.
    # Packets written to the device should be packets that are sent from AV
    # test_packet = AVtoGCSData2()
    # test_packets = [AVtoGCSData1(), AVtoGCSData2(), AVtoGCSData3(),
    #                 GCStoAVStateCMD(), GCStoGSEStateCMD(), GSEtoGCSData1(), GSEtoGCSData2()]

    # # [3, 4, 5, 1, 2, 6, 7]
    # slogger.debug(f"ID Orders: {[x.ID for x in test_packets]}")

    LOCK_PATH = config.load_config()['locks']['lock_file_gse_response_path']
    try:
        while True:
            # Pretending to be GSE for today
            for packet in [GSEtoGCSData1(), GSEtoGCSData2()]:
                # As a cheeky emulation, only write when the lock file is PRESENT
                if os.path.exists(LOCK_PATH):
                    packet.write_payload()
                    # Not sure if this needs to be longer?
                    time.sleep(0.190)  # Real timing is about 200-250ms.
            # slogger.debug("Looped through all packets")
            slogger.debug("Looped through all packets")
            time.sleep(3)
    except KeyboardInterrupt:
        # As soon as the CLI gets the interrupt, a race condition starts and child cleanup is not guaranteed
        slogger.debug("Emulator interrupted by user")

    slogger.debug("Emulator finished")


if __name__ == '__main__':
    main()
