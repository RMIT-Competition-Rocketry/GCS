from typing import Annotated, Literal
import math


class Metric:
    """The metric class will generate byte payloads to be used by the device emulator.
    AFAIK everything is little endian"""

    SIGNED_INT = Annotated[int, Literal['signed']]

    @staticmethod
    def _invert_bits(num: int) -> int:
        num_bits = num.bit_length()  # Get the number of bits required to represent num
        # Create a bitmask of the same length (all 1s)
        MASK = (1 << num_bits) - 1
        return ~num & MASK           # Invert bits and apply mask

    @staticmethod
    def _invert_bytes(data: bytes) -> bytes:
        if len(data) != 1:
            raise ValueError("Input must be a single byte.")
        return bytes([~data[0] & 0xFF])

    @staticmethod
    def _int_to_byte(value: int) -> bytes:
        """Converts an integer to a single byte (8 bits). Raises ValueError if out of range."""
        if not (0 <= value <= 0xFF):  # 0xFF == 255 (8-bit max)
            raise ValueError("Value must be between 0 and 255 (8-bit range).")
        # Convert to a single byte
        return value.to_bytes(1, byteorder='little')

    @staticmethod
    def _int_to_multiple_bytes(value: int, NUM_BYTES: int) -> bytes:
        """Converts an integer to a specified number of bytes.

        Args:
            value (int): The integer to convert.
            num_bytes (int): The number of bytes to convert the integer into.

        Returns:
            bytes: The integer represented as bytes.

        Raises:
            ValueError: If the value is out of range for the specified number of bytes.
        """
        # Calculate the maximum value for the given number of bytes
        # Equivalent to 2^(8*num_bytes) - 1
        max_value = (1 << (8 * NUM_BYTES)) - 1

        # Check if the value is within the valid range
        if not (0 <= value <= max_value):
            raise ValueError(
                f"Value must be between 0 and {max_value} for {NUM_BYTES} byte(s).")

        # Convert the integer to the specified number of bytes
        return value.to_bytes(NUM_BYTES, byteorder='little')

    @staticmethod
    def is_valid_int16(VALUE: int) -> bool:
        """Check if a value is within the valid range of a 2-byte integer (int16)."""
        return -32_768 <= VALUE <= 32_767

    @staticmethod
    def is_valid_float32(VALUE: float) -> bool:
        """Check if a value is within the valid range of a 32-bit float.

        Args:
            VALUE (float): The value to check.

        Returns:
            bool: True if the value is a valid 32-bit float, False otherwise.
        """

        return -3.4028235e+38 <= VALUE <= 3.4028235e+38 and not math.isinf(VALUE) and not math.isnan(VALUE)

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

        result = (result << 3) | 0b1010  # Add fixed bits
        result = (result << 1) | MAIN_SECONDARY_TEST
        result = (result << 1) | MAIN_PRIMARY_TEST
        result = (result << 1) | APOGEE_SECONDARY_TEST
        result = (result << 1) | APROGEE_PRIMARY_TEST

        return Metric._int_to_byte(result)

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
        result = (result << 3) | 0b1010  # Add fixed bits
        result = (result << 1) | APOGEE_PRIMARY_TEST_RESULTS
        result = (result << 1) | APOGEE_SECONDARY_TEST_RESULTS

        return Metric._int_to_byte(result)

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
        result = (result << 3) | 0b1010  # Add fixed bits
        result = (result << 1) | MAIN_PRIMARY_TEST_RESULTS
        result = (result << 1) | MAIN_SECONDARY_TEST_RESULTS

        return Metric._int_to_byte(result)

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

        return Metric._invert_bytes(Metric.continuityCheckCMDFlags(
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

        return Metric._int_to_byte(result)

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

        return Metric._int_to_byte(result)

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

        return Metric._int_to_byte(result)

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
        if not Metric.is_valid_int16(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes(VALUE, 2)

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

        if not Metric.is_valid_int16(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes(VALUE, 2)

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

        if not Metric.is_valid_int16(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes(VALUE, 2)

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

        if not Metric.is_valid_int16(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes(VALUE, 2)

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

        if not Metric.is_valid_int16(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes(VALUE, 2)

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

        if not Metric.is_valid_int16(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes(VALUE, 2)

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

        if not Metric.is_valid_int16(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes(VALUE, 2)

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

        if not Metric.is_valid_int16(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes(VALUE, 2)

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

        if not Metric.is_valid_int16(VALUE):
            raise ValueError(
                "Value must be between -32768 and 32767 (16-bit signed range).")

        return Metric._int_to_multiple_bytes(VALUE, 2)

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

        return Metric._int_to_multiple_bytes(VALUE, 4)

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

        return Metric._int_to_multiple_bytes(VALUE, 4)
