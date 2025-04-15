from rocket_sim import flight_simulation
from backend.tools.device_emulator import AVtoGCSData1, MockPacket
import sys
import time
import pandas as pd
import backend.process_logging as slogger
import config.config as config
import configparser

# Setting up the config
cfg = configparser.ConfigParser()
cfg.read("config/simulation.ini")
sim_cfg = cfg["Simulation"]
TIMEOUT_INTERVAL = float(sim_cfg["timeout_interval"])


def send_simulated_packet(altitude: float, speed: float, w1: float, w2: float, w3: float, ax: float, ay: float, az: float):
    """
    Sends a simulated telemetry packet with the provided sensor values.

    Parameters:
    - altitude (float): Altitude of the rocket in meters.
    - speed (float): Speed of the rocket in meters per second.
    - w1, w2, w3 (float): Angular velocity readings (typically from a gyroscope).
      These should be divided by 0.00875 to convert to degrees per second.
    - ax, ay, az (float): Acceleration readings (typically from an accelerometer).
      These should be converted from m/s^2 to g-force units (divide by 9.80665).

    Notes:
    - The conversion is currently being done in this function so don't worry about that
    - The packet format and transmission method should match the backend
    """
    packet = AVtoGCSData1(
        FLIGHT_STATE_MSB=False,
        FLIGHT_STATE_1=False,
        FLIGHT_STATE_LSB=False,
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG=False,
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY=False,
        GPS_FIX_FLAG=False,
        PAYLOAD_CONNECTION_FLAG=True,
        CAMERA_CONTROLLER_CONNECTION=True,
        ACCEL_LOW_X=int(2048*ax),
        ACCEL_LOW_Y=int(ay / 9.81 * 2048),
        ACCEL_LOW_Z=int(az / 9.81 * 2048),
        ACCEL_HIGH_X=int(ax / 9.81 * -1048),
        ACCEL_HIGH_Y=int(ay / 9.81 * -1048),
        ACCEL_HIGH_Z=int(ay / 9.81 * 1048),
        GYRO_X=int(w1/0.00875),
        GYRO_Y=int(w2/0.00875),
        GYRO_Z=int(w3/0.00875),
        ALTITUDE=altitude,
        VELOCITY=speed,
        APOGEE_PRIMARY_TEST_COMPETE=True,
        APOGEE_SECONDARY_TEST_COMPETE=False,
        APOGEE_PRIMARY_TEST_RESULTS=False,
        APOGEE_SECONDARY_TEST_RESULTS=False,
        MAIN_PRIMARY_TEST_COMPETE=True,
        MAIN_SECONDARY_TEST_COMPETE=False,
        MAIN_PRIMARY_TEST_RESULTS=False,
        MAIN_SECONDARY_TEST_RESULTS=False,
        MOVE_TO_BROADCAST=False
    )
    packet.write_payload()


def isImportantPacket(current_row, last_row):
    """
        Takes in two dataframe rows, this function simply determines if the flight state is different indicating that its an important packet
    """
    if last_row is None:
        return True
    if current_row["flight_state"] != last_row["flight_state"]:
        return True

    # @TODO More important calculations


def run_emulator(FLIGHT_DATA: pd.DataFrame, DEVICE_NAME: str):
    """
        Runs the emulator based on the flight data
    """
    # Init mockpacket
    MockPacket.initialize_settings(
        config.load_config()['emulation'], FAKE_DEVICE_NAME=DEVICE_NAME)

    # Getting the last few rows
    last_time = -1
    last_row = None
    # Filteration and sending packets
    for _, row in FLIGHT_DATA.iterrows():
        current_time = row["# Time (s)"]
        slogger.info(str(current_time))
        # Simply check if there's been enough time or that there is an important packet
        if (current_time - last_time) >= TIMEOUT_INTERVAL or isImportantPacket(current_row=row, last_row=last_row):
            send_simulated_packet(
                row[" Altitude AGL (m)"],
                row[" Speed - Velocity Magnitude (m/s)"],
                row[" ω1 (rad/s)"],
                row[" ω2 (rad/s)"],
                row[" ω3 (rad/s)"],
                row[" Ax (m/s²)"],
                row[" Ay (m/s²)"],
                row[" Az (m/s²)"]
            )
            last_time = current_time
            last_row = row

        time.sleep(TIMEOUT_INTERVAL)


def main():
    slogger.info("Emulator Starting Simulation...")
    try:
        # @TODO PLEASE EDIT THIS DEVICE NAME ITS JUST COPIED STRAIGHT FROM EMULATOR
        try:
            FAKE_DEVICE_NAME = sys.argv[sys.argv.index('--device-rocket') + 1]
        except ValueError:
            slogger.error(
                "Failed to find device names in arguments for simulator")
            raise
        FLIGHT_DATA = flight_simulation.get_simulated_flight_data()
        run_emulator(FLIGHT_DATA, FAKE_DEVICE_NAME)
    except Exception as e:
        # @TODO Add more debugs
        slogger.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
