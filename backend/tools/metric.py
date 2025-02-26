from typing import Annotated, Literal
import math
import struct


class Metric:
    """The metric class will generate byte payloads to be used by the device emulator.
    AFAIK everything is big endian"""

    SIGNED_INT = Annotated[int, Literal['signed']]
    UNSIGNED_INT = Annotated[int, Literal['unsigned']]

    @staticmethod
    def _invert_bits(num: int) -> int:
        num_bits = num.bit_length()  # Get the number of bits required to represent num
        # Create a bitmask of the same length (all 1s)
        MASK = (1 << num_bits) - 1
        return ~num & MASK           # Invert bits and apply mask

    @staticmethod
    def _invert_byte(data: bytes) -> bytes:
        if len(data) != 1:
            raise ValueError("Input must be a single byte.")
        return bytes([~data[0] & 0xFF])

    @staticmethod
    def _float_to_bytes(value: float, NUM_BYTES: int = 4) -> bytes:
        """Converts a float to bytes (default 32-bit/4 bytes).

        Args:
            value (float): The float value to convert
            NUM_BYTES (int): Number of bytes (4 for float32, 8 for float64)

        Returns:
            bytes: The float represented as bytes

        Raises:
            ValueError: If NUM_BYTES is not 4 (float32) or 8 (float64)
        """

        if NUM_BYTES == 4:
            # https://docs.python.org/3/library/struct.html#byte-order-size-and-alignment
            return struct.pack('>f', value)  # big-endian float32
        elif NUM_BYTES == 8:  # Double?
            return struct.pack('>d', value)  # big-endian float64
        else:
            raise ValueError("NUM_BYTES must be 4 (float32) or 8 (float64)")

    @staticmethod
    def _float32_to_bytes(value: float) -> bytes:
        """Converts a float to a 32-bit (4 byte) representation.

        Args:
            value (float): The float value to convert

        Returns:
            bytes: The float32 represented as 4 bytes

        Raises:
            ValueError: If value cannot be represented as float32
        """
        if not Metric.is_valid_float32(value):
            raise ValueError("Value must be a valid 32-bit float")
        return Metric._float_to_bytes(value, 4)

    @staticmethod
    def _float64_to_bytes(value: float) -> bytes:
        """Converts a float to a 64-bit (8 byte) representation.

        Args:
            value (float): The float value to convert

        Returns:
            bytes: The float64 represented as 8 bytes
        """
        return Metric._float_to_bytes(value, 8)

    @staticmethod
    def _int_to_byte_unsigned(value: int) -> bytes:
        """Converts an unsigned integer to a single byte (8 bits).

        Args:
            value (int): The unsigned integer to convert (0-255).

        Returns:
            bytes: The integer represented as a single byte.

        Raises:
            ValueError: If value is outside the valid unsigned byte range.
        """
        if not (0 <= value <= 0xFF):  # 0xFF == 255 (8-bit max)
            raise ValueError(
                "Value must be between 0 and 255 (8-bit unsigned range).")
        return value.to_bytes(1, byteorder='big', signed=False)

    @staticmethod
    def _int_to_byte_signed(value: int) -> bytes:
        """Converts a signed integer to a single byte (8 bits).

        Args:
            value (int): The signed integer to convert (-128 to 127).

        Returns:
            bytes: The integer represented as a single byte.

        Raises:
            ValueError: If value is outside the valid signed byte range.
        """
        if not (-128 <= value <= 127):
            raise ValueError(
                "Value must be between -128 and 127 (8-bit signed range).")
        return value.to_bytes(1, byteorder='big', signed=True)

    @staticmethod
    def _int_to_multiple_bytes_unsigned(value: int, NUM_BYTES: int) -> bytes:
        """Converts an unsigned integer to a specified number of bytes.

        Args:
            value (int): The unsigned integer to convert.
            NUM_BYTES (int): The number of bytes to convert the integer into.

        Returns:
            bytes: The integer represented as bytes.

        Raises:
            ValueError: If the value is out of range for the specified number of bytes.
        """
        max_value = (1 << (8 * NUM_BYTES)) - 1

        if not (0 <= value <= max_value):
            raise ValueError(
                f"Value must be between 0 and {max_value} for {NUM_BYTES} byte(s).")

        return value.to_bytes(NUM_BYTES, byteorder='big', signed=False)

    @staticmethod
    def _int_to_multiple_bytes_signed(value: int, NUM_BYTES: int) -> bytes:
        """Converts a signed integer to a specified number of bytes.

        Args:
            value (int): The signed integer to convert.
            NUM_BYTES (int): The number of bytes to convert the integer into.

        Returns:
            bytes: The integer represented as bytes.

        Raises:
            ValueError: If the value is out of range for the specified number of bytes.
        """
        max_value = (1 << (8 * NUM_BYTES - 1)) - 1
        min_value = -(1 << (8 * NUM_BYTES - 1))

        if not (min_value <= value <= max_value):
            raise ValueError(
                f"Value must be between {min_value} and {max_value} for {NUM_BYTES} byte(s).")

        return value.to_bytes(NUM_BYTES, byteorder='big', signed=True)

    @staticmethod
    def is_valid_int16_singed(VALUE: int) -> bool:
        """Check if a value is within the valid range of a signed 2-byte integer (int16)."""
        if not isinstance(VALUE, int):
            return False
        return -32_768 <= VALUE <= 32_767

    @staticmethod
    def is_valid_int16_unsigned(VALUE: int) -> bool:
        """Check if a value is within the valid range of an unsigned 2-byte integer (uint16)."""
        if not isinstance(VALUE, int):
            return False
        return 0 <= VALUE <= 65_535

    @staticmethod
    def is_valid_float32(VALUE: float) -> bool:
        """Check if a value is within the valid range of a 32-bit float. All floats are signed

        Args:
            VALUE (float): The value to check.

        Returns:
            bool: True if the value is a valid 32-bit float, False otherwise.
        """
        if not isinstance(VALUE, (int, float)):
            return False
        return (-3.4028235e+38 <= VALUE <= 3.4028235e+38 and
                not math.isinf(VALUE) and
                not math.isnan(VALUE))

    @staticmethod
    def is_valid_float64(VALUE: float) -> bool:
        """Check if a value is within the valid range of a 64-bit float.

        Args:
            VALUE (float): The value to check.

        Returns:
            bool: True if the value is a valid 64-bit float, False otherwise.
        """
        if not isinstance(VALUE, (int, float)):
            return False
        return (not math.isinf(VALUE) and
                not math.isnan(VALUE))

    @staticmethod
    def dummyByte() -> bytes:
        """ Just returns 0x00 """
        result = 0
        return Metric._int_to_byte_unsigned(result)

    @staticmethod
    def continuityCheckCMDFlags(
        MAIN_SECONDARY_TEST: bool,
        MAIN_PRIMARY_TEST: bool,
        APOGEE_SECONDARY_TEST: bool,
        APROGEE_PRIMARY_TEST: bool,
    ) -> bytes:
        """_summary_

        Args:
            mainSecondaryTest (bool): (0 = Do not do test, 1 = do test)
            mainPrimaryTest (bool): (0 = Do not do test, 1 = do test)
            apogeeSecondaryTest (bool): (0 = Do not do test, 1 = do test)
            apogeePrimaryTest (bool): (0 = Do not do test, 1 = do test)

        Returns:
            int: Test flags prefixed with filler bits
        """
        result = 0

        result = (result << 4) | 0b1010  # Add fixed bits
        result = (result << 1) | MAIN_SECONDARY_TEST
        result = (result << 1) | MAIN_PRIMARY_TEST
        result = (result << 1) | APOGEE_SECONDARY_TEST
        result = (result << 1) | APROGEE_PRIMARY_TEST

        return Metric._int_to_byte_unsigned(result)

    @staticmethod
    def continuityCheckResultsApogee(
        APOGEE_PRIMARY_TEST_COMPETE: bool,
        APOGEE_SECONDARY_TEST_COMPETE: bool,
        APOGEE_PRIMARY_TEST_RESULTS: bool,
        APOGEE_SECONDARY_TEST_RESULTS: bool,
    ) -> bytes:
        """_summary_

        Note 4

        Args:
            APOGEE_PRIMARY_TEST_COMPETE (bool): (0 = not complete, 1 = complete)
            APOGEE_SECONDARY_TEST_COMPETE (bool): (0 = not complete, 1 = complete)
            APOGEE_PRIMARY_TEST_RESULTS (bool): (0 = No Continuity, 1 = Continuity)
            APOGEE_SECONDARY_TEST_RESULTS (bool): (0 = No Continuity, 1 = Continuity)

        Returns:    
            int: Test flags prefixed with filler bits
        """
        result = 0

        result = (result << 1) | APOGEE_PRIMARY_TEST_COMPETE
        result = (result << 1) | APOGEE_SECONDARY_TEST_COMPETE
        result = (result << 4) | 0b1010  # Add fixed bits
        result = (result << 1) | APOGEE_PRIMARY_TEST_RESULTS
        result = (result << 1) | APOGEE_SECONDARY_TEST_RESULTS

        return Metric._int_to_byte_unsigned(result)

    @staticmethod
    def continuityCheckResultsMain(
        MAIN_PRIMARY_TEST_COMPETE: bool,
        MAIN_SECONDARY_TEST_COMPETE: bool,
        MAIN_PRIMARY_TEST_RESULTS: bool,
        MAIN_SECONDARY_TEST_RESULTS: bool,
    ) -> bytes:
        """_summary_

        Note 5

        Args:
            MAIN_PRIMARY_TEST_COMPETE (bool): (0 = not complete, 1 = complete)
            MAIN_SECONDARY_TEST_COMPETE (bool): (0 = not complete, 1 = complete)
            MAIN_PRIMARY_TEST_RESULTS (bool): (0 = No Continuity, 1 = Continuity)
            MAIN_SECONDARY_TEST_RESULTS (bool): (0 = No Continuity, 1 = Continuity)

        Returns:    
            int: Test flags prefixed with filler bits
        """
        result = 0

        result = (result << 1) | MAIN_PRIMARY_TEST_COMPETE
        result = (result << 1) | MAIN_SECONDARY_TEST_COMPETE
        result = (result << 4) | 0b1010  # Add fixed bits
        result = (result << 1) | MAIN_PRIMARY_TEST_RESULTS
        result = (result << 1) | MAIN_SECONDARY_TEST_RESULTS

        return Metric._int_to_byte_unsigned(result)

    @staticmethod
    def continuityCheckCMDFlagsINVERTED(
        MAIN_SECONDARY_TEST: bool,
        MAIN_PRIMARY_TEST: bool,
        APOGEE_SECONDARY_TEST: bool,
        APROGEE_PRIMARY_TEST: bool,
    ) -> int:
        """ Output of regular continuityCheckCMDFlags but every bit is inverted 

        Args:
            mainSecondaryTest(bool): (0=Do not do test, 1=do test)
            mainPrimaryTest(bool): (0=Do not do test, 1=do test)
            apogeeSecondaryTest(bool): (0=Do not do test, 1=do test)
            apogeePrimaryTest(bool): (0=Do not do test, 1=do test)

        Returns:
            int: Test flags prefixed with filler bits
        """

        return Metric._invert_byte(Metric.continuityCheckCMDFlags(
            MAIN_SECONDARY_TEST,
            MAIN_PRIMARY_TEST,
            APOGEE_SECONDARY_TEST,
            APROGEE_PRIMARY_TEST,
        ))

    @staticmethod
    def BroadcastBeginCMDFlags(
        BEGIN_BRAODCAST: bool,
    ) -> bytes:
        """_summary_

        Args:
            BEGIN_BRAODCAST (bool): 0 = Do not begin broadcast, 1 = begin broadcast

        Returns:
            bytes: _description_
        """
        result = 0xFF if BEGIN_BRAODCAST else 0x00

        return Metric._int_to_byte_unsigned(result)

    @staticmethod
    def MovingToBroadCastFlag(
        MOVE_TO_BRAODCAST: bool,
    ) -> bytes:
        """

        Note 6

        Args:
            MOVE_TO_BRAODCAST (bool): 0 = No not move, 1 = Move to broadcast

        Returns:
            bytes: _description_
        """
        result = 0b10101010 if MOVE_TO_BRAODCAST else 0b00000000

        return Metric._int_to_byte_unsigned(result)

    @staticmethod
    def StateSetFlags2p1(
        MANUAL_PURGE: bool,
        O2_FILL_ACTIVATE: bool,
        SELECTOR_SWITCH_NEUTRAL_POSITION: bool,
        N2O_FILL_ACTIVATE: bool,
        IGNITION_FIRE: bool,  # https://youtu.be/Vmm_Kq1EN8k?si=GEpc8AoEhRgRrFRI
        IGNITION_SELECTED: bool,
        GAS_FILL_SELECTED: bool,
        SYSTEM_ACTIVATE: bool,
    ) -> bytes:
        """_summary_

        Args:
            MANUAL_PURGE (bool): 0 = no, 1 = yes
            O2_FILL_ACTIVATE (bool): 0 = no, 1 = yes
            SELECTOR_SWITCH_NEUTRAL_POSITION (bool): 0 = no, 1 = yes
            N2O_FILL_ACTIVATE (bool): 0 = no, 1 = yes
            IGNITION_FIRE (bool): 0 = no, 1 = yes
            IGNITION_SELECTED (bool): 0 = no, 1 = yes
            GAS_FILL_SELECTED (bool): 0 = no, 1 = yes
            SYSTEM_ACTIVATE (bool): 0 = disable, 1 = enabled

        Returns:
            bytes: _description_
        """

        result = 0
        result = (result << 1) | MANUAL_PURGE
        result = (result << 1) | O2_FILL_ACTIVATE
        result = (result << 1) | SELECTOR_SWITCH_NEUTRAL_POSITION
        result = (result << 1) | N2O_FILL_ACTIVATE
        result = (result << 1) | IGNITION_FIRE
        result = (result << 1) | IGNITION_SELECTED
        result = (result << 1) | GAS_FILL_SELECTED
        result = (result << 1) | SYSTEM_ACTIVATE

        return Metric._int_to_byte(result)

    @staticmethod
    def StateSetFlagINVERTEDs2p2(
        MANUAL_PURGE: bool,
        O2_FILL_ACTIVATE: bool,
        SELECTOR_SWITCH_NEUTRAL_POSITION: bool,
        N2O_FILL_ACTIVATE: bool,
        IGNITION_FIRE: bool,  # https://youtu.be/Vmm_Kq1EN8k?si=GEpc8AoEhRgRrFRI
        IGNITION_SELECTED: bool,
        GAS_FILL_SELECTED: bool,
        SYSTEM_ACTIVATE: bool,
    ) -> bytes:
        """_summary_

        Args:
            MANUAL_PURGE (bool): 0 = no, 1 = yes
            O2_FILL_ACTIVATE (bool): 0 = no, 1 = yes
            SELECTOR_SWITCH_NEUTRAL_POSITION (bool): 0 = no, 1 = yes
            N2O_FILL_ACTIVATE (bool): 0 = no, 1 = yes
            IGNITION_FIRE (bool): 0 = no, 1 = yes
            IGNITION_SELECTED (bool): 0 = no, 1 = yes
            GAS_FILL_SELECTED (bool): 0 = no, 1 = yes
            SYSTEM_ACTIVATE (bool): 0 = disable, 1 = enabled

        Returns:
            bytes: _description_
        """

        result = Metric.StateSetFlags2p1(
            MANUAL_PURGE,
            O2_FILL_ACTIVATE,
            SELECTOR_SWITCH_NEUTRAL_POSITION,
            N2O_FILL_ACTIVATE,
            IGNITION_FIRE,
            IGNITION_SELECTED,
            GAS_FILL_SELECTED,
            SYSTEM_ACTIVATE,
        )

        return Metric._invert_byte(result)

    @staticmethod
    def StateFlags3p0(
        FLIGHT_STATE_MSB: bool,
        FLIGHT_STATE_1: bool,
        FLIGHT_STATE_LSB: bool,
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG: bool,
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY: bool,
        GPS_FIX_FLAG: bool,
        PAYLOAD_CONNECTION_FLAG: bool,
        CAMERA_CONTROLLER_CONNECTION: bool,
    ) -> bytes:
        """_summary_

        Note 3, A

        Flight state is a 3 bit number. 
        Pass it bit by bit. #lol

        Note A:
        0b000 = Pre-flight - No Flight Ready
        0b001 = Pre-Flight - Flight Ready
        0b010 = Launch	0b011 = Coast	0b100 = Apogee

        Args:
            FLIGHT_STATE_MSB (bool): See note A
            FLIGHT_STATE_1 (bool): See note A
            FLIGHT_STATE_LSB (bool): See note A
            DUAL_BOARD_CONNECTIVITY_STATE_FLAG (bool): (0 = Only 1 Board Connected, 1 = 2x Australis Boards Connected)
            RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY (bool): (0 = not flight ready, 1 = flight ready)
            GPS_FIX_FLAG (bool): (0 = No Fix, 1 = Fixed)
            PAYLOAD_CONNECTION_FLAG (bool): (0 = NC, 1= Connected)
            CAMERA_CONTROLLER_CONNECTION (bool): (0 = NC, 1 = Connected)

        Returns:
            bytes: _description_
        """

        result = 0
        result = (result << 1) | FLIGHT_STATE_MSB
        result = (result << 1) | FLIGHT_STATE_1
        result = (result << 1) | FLIGHT_STATE_LSB
        result = (result << 1) | DUAL_BOARD_CONNECTIVITY_STATE_FLAG
        result = (result << 1) | RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY
        result = (result << 1) | GPS_FIX_FLAG
        result = (result << 1) | PAYLOAD_CONNECTION_FLAG
        result = (result << 1) | CAMERA_CONTROLLER_CONNECTION

        return Metric._int_to_byte_unsigned(result)

    @staticmethod
    def ACCEL_LOW_X(
        VALUE: SIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (SIGNED_INT16): 16bit signed int. Float after calculation

        Returns:
            bytes: _description_
        """
        if not Metric.is_valid_int16_singed(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes_signed(VALUE, 2)

    @staticmethod
    def ACCEL_LOW_Y(
        VALUE: SIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (SIGNED_INT16): 16bit signed int. Float after calculation

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_int16_singed(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes_signed(VALUE, 2)

    @staticmethod
    def ACCEL_LOW_Z(
        VALUE: SIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (SIGNED_INT16): 16bit signed int. Float after calculation

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_int16_singed(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes_signed(VALUE, 2)

    @staticmethod
    def ACCEL_HIGH_X(
        VALUE: SIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (SIGNED_INT16): 16bit signed int. Float after calculation

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_int16_singed(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes_signed(VALUE, 2)

    @staticmethod
    def ACCEL_HIGH_Y(
        VALUE: SIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (SIGNED_INT16): 16bit signed int. Float after calculation

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_int16_singed(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes_signed(VALUE, 2)

    @staticmethod
    def ACCEL_HIGH_Z(
        VALUE: SIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (SIGNED_INT16): 16bit signed int. Float after calculation

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_int16_singed(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes_signed(VALUE, 2)

    @staticmethod
    def GYRO_X(
        VALUE: SIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (SIGNED_INT16): 16bit signed int. Float after calculation

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_int16_singed(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes_signed(VALUE, 2)

    @staticmethod
    def GYRO_Y(
        VALUE: SIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (SIGNED_INT16): 16bit signed int. Float after calculation

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_int16_singed(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes_signed(VALUE, 2)

    @staticmethod
    def GYRO_Z(
        VALUE: SIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (SIGNED_INT16): 16bit signed int. Float after calculation

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_int16_singed(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes_signed(VALUE, 2)

    @staticmethod
    def ALTITUDE(
        VALUE: float,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (float): 32bit float. 

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_float32(VALUE):
            raise ValueError("Value must be a valid 32-bit float.")

        return Metric._float32_to_bytes(VALUE)

    @staticmethod
    def VELOCITY(
        VALUE: float,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (float): 32bit float. 

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_float32(VALUE):
            raise ValueError("Value must be a valid 32-bit float.")

        return Metric._float32_to_bytes(VALUE)

    @staticmethod
    def GPS(LATITUDE: str, LONGITUDE: str) -> bytes:
        """GPS coordinate char bytes

        Args:
            LATITUDE (str): 15 char string
            LONGITUDE (str): 15 char string

        Raises:
            ValueError: Raised if string length != 15

        Returns:
            bytes: Byte output
        """
        if not (
            isinstance(LATITUDE, str) and isinstance(LONGITUDE, str)
            and len(LATITUDE) == 15 and len(LONGITUDE) == 15
        ):
            raise ValueError("Latitude and longitude must be 15 char strings.")

        # No null bytes here I think
        return bytes(LATITUDE + LONGITUDE, 'utf-8')

    @staticmethod
    def TRANSDUCER(
        VALUE: float,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (float): 32bit float. 

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_float32(VALUE):
            raise ValueError("Value must be a valid 32-bit float.")

        return Metric._float32_to_bytes(VALUE)

    @staticmethod
    def THERMOCOUPLE(
        VALUE: float,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (float): 32bit float. 

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_float32(VALUE):
            raise ValueError("Value must be a valid 32-bit float.")

        return Metric._float32_to_bytes(VALUE)

    @staticmethod
    def ERROR_CODE_GSE(
        IGNITION_ERROR: bool,
        RELAY3_ERROR: bool,
        RELAY2_ERROR: bool,
        RELAY1_ERROR: bool,
        THERMOCOUPLE_4_ERROR: bool,
        THERMOCOUPLE_3_ERROR: bool,
        THERMOCOUPLE_2_ERROR: bool,
        THERMOCOUPLE_1_ERROR: bool,
        LOAD_CELL_4_ERROR: bool,
        LOAD_CELL_3_ERROR: bool,
        LOAD_CELL_2_ERROR: bool,
        LOAD_CELL_1_ERROR: bool,
        TRANSDUCER_4_ERROR: bool,
        TRANSDUCER_3_ERROR: bool,
        TRANSDUCER_2_ERROR: bool,
        TRANSDUCER_1_ERROR: bool,
    ) -> bytes:
        result = 0
        result = (result << 1) | IGNITION_ERROR
        result = (result << 1) | RELAY3_ERROR
        result = (result << 1) | RELAY2_ERROR
        result = (result << 1) | RELAY1_ERROR
        result = (result << 1) | THERMOCOUPLE_4_ERROR
        result = (result << 1) | THERMOCOUPLE_3_ERROR
        result = (result << 1) | THERMOCOUPLE_2_ERROR
        result = (result << 1) | THERMOCOUPLE_1_ERROR
        result = (result << 1) | LOAD_CELL_4_ERROR
        result = (result << 1) | LOAD_CELL_3_ERROR
        result = (result << 1) | LOAD_CELL_2_ERROR
        result = (result << 1) | LOAD_CELL_1_ERROR
        result = (result << 1) | TRANSDUCER_4_ERROR
        result = (result << 1) | TRANSDUCER_3_ERROR
        result = (result << 1) | TRANSDUCER_2_ERROR
        result = (result << 1) | TRANSDUCER_1_ERROR

        return Metric._int_to_multiple_bytes_unsigned(result, 2)

    @staticmethod
    def INTERNAL_TEMP_GSE(
        VALUE: float,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (float): 32bit float. 

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_float32(VALUE):
            raise ValueError("Value must be a valid 32-bit float.")

        return Metric._float32_to_bytes(VALUE)

    @staticmethod
    def WIND_SPEED_GSE(
        VALUE: float,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (float): 32bit float. 

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_float32(VALUE):
            raise ValueError("Value must be a valid 32-bit float.")

        return Metric._float32_to_bytes(VALUE)

    @staticmethod
    def GAS_BOTTLE_WEIGHT(
        VALUE: UNSIGNED_INT,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (UNSIGNED_INT16): 16bit unsigned int.

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_int16_unsigned(VALUE):
            raise ValueError(
                "Value must be between 0, 65_535 (16-bit unsigned range).")

        return Metric._int_to_multiple_bytes_unsigned(VALUE, 2)

    @staticmethod
    def ADDITIONAL_VA_INPUT(
        VALUE: float,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (float): 32bit float. 

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_float32(VALUE):
            raise ValueError("Value must be a valid 32-bit float.")

        return Metric._float32_to_bytes(VALUE)

    @staticmethod
    def ADDITIONAL_CURRENT_INPUT(
        VALUE: float,
    ) -> bytes:
        """_summary_

        Args:
            VALUE (float): 32bit float.  Must be between 4-20mA?

        Returns:
            bytes: _description_
        """

        if not Metric.is_valid_float32(VALUE):
            raise ValueError("Value must be a valid 32-bit float.")

        return Metric._float32_to_bytes(VALUE)
