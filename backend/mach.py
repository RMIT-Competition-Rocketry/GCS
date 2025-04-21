from numbers import Number
import backend.process_logging as slogger
import math

# Provides methods to generate accurate mach values


class Mach:
    @staticmethod
    def sound_speed(TEMPERATURE: Number) -> float:
        """Returns the speed of sound based on temperature

        Args:
            TEMPERATURE (Number): Temperature in kelvin

        Returns:
            float: Speed of sound in meters/second
        """
        R = 8.3145  # Molar gas constant
        Y = 1.4  # Adiabatic index
        M = 0.0289645  # Molar mass for air
        return math.sqrt((R*Y*TEMPERATURE)/(M))

    @staticmethod
    def isa_temp(ALTITUDE_M: Number) -> float:
        """Calculate the ISA based temperature at a given altitude.
        https://agodemar.github.io/FlightMechanics4Pilots/assets/img/ISA_Temperature.png

        Args:
            ALTITUDE_M (Number): Altitude in meters

        Returns:
            float: temperature in kelvin
        """
        if ALTITUDE_M < -20:
            slogger.error(
                f"Altitude should be above ground for accurate mach calculation: {ALTITUDE_M}")

        if ALTITUDE_M < 11000:
            # Legacy won't go past 3km anyway
            return 288.15 - (0.0065 * ALTITUDE_M)
        elif ALTITUDE_M < 20000:
            return 216.65
        elif ALTITUDE_M < 32000:
            return 216.65 + (0.001 * (ALTITUDE_M - 20000))
        elif ALTITUDE_M < 47000:
            return 228.65 + (0.0028 * (ALTITUDE_M - 32000))
        elif ALTITUDE_M < 51000:
            return 270.65
        elif ALTITUDE_M < 71000:
            return 270.65 + (-0.0028 * (ALTITUDE_M - 51000))
        elif ALTITUDE_M < 84852:
            return 214.65 + (-0.002 * (ALTITUDE_M - 71000))
        elif ALTITUDE_M < 90000:
            return 186.95
        else:
            return 186.95 + (0.004 * (ALTITUDE_M - 90000))

    @staticmethod
    def mach_from_alt_estimate(VELOCITY_M: Number, ALTITUDE_M: Number) -> float:
        """Returns velocity in mach

        Args:
            VELOCITY_M (Number): Velocity in meters/second
            ALTITUDE_M (Number): Altitude in meters

        Returns:
            float: Mach speed 
        """
        return VELOCITY_M/Mach.sound_speed(Mach.isa_temp(ALTITUDE_M))
