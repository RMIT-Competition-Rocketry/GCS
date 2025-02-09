
class Metric:
    """The metric class will generate byte payloads to be used by the device emulator.
    AFAIK everything is little endian"""

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
