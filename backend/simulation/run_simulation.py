from rocket_sim import flight_simulation
from backend.tools.device_emulator import AVtoGCSData1, MockPacket
from itertools import count
import math
import sys
import pandas as pd
import time
import backend.includes_python.process_logging as slogger
import backend.includes_python.service_helper as service_helper
import config.config as config
import configparser


# Setting up the config
cfg = configparser.ConfigParser()
cfg.read("config/simulation.ini")
sim_cfg = cfg["Simulation"]
# In seconds
TIMEOUT_INTERVAL_MS = float(sim_cfg["timeout_interval_ms"])
MS_PER_SECOND = 1000


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
        ACCEL_LOW_X=int(ax / 9.81 * 2048),
        ACCEL_LOW_Y=int(ay / 9.81 * 2048),
        ACCEL_LOW_Z=int(az / 9.81 * 2048),
        ACCEL_HIGH_X=int(ax / 9.81 * -1048),
        ACCEL_HIGH_Y=int(ay / 9.81 * -1048),
        ACCEL_HIGH_Z=int(az / 9.81 * 1048),
        GYRO_X=int(math.degrees(w1)/0.00875),
        GYRO_Y=int(math.degrees(w2)/0.00875),
        GYRO_Z=int(math.degrees(w3)/0.00875),

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
        MOVE_TO_BROADCAST=True
    )
    # https://github.com/RMIT-Competition-Rocketry/GCS/issues/114
    time.sleep(0.01)  # Allow the buffer to update
    packet.write_payload()


def packet_importance(PACKET, PREVIOUS_WINDOW_TRAILER) -> int:
    """
        Returns a numerical score on how 'important' the packet is
        We don't want to drop these packets 

        Args:
            PACKET (type): Current packet for observation
            PREVIOUS_WINDOW_TRAILER (type): Last packet in previous window
    """
    importance = 0

    last_window_state = PREVIOUS_WINDOW_TRAILER["flight_state"]
    current_packet_state = PACKET["flight_state"]

    # Increase score if this packet has a different flight state than last window
    if last_window_state is None or last_window_state != current_packet_state:
        importance += 1

    return importance


def partition_into_windows(FLIGHT_DATA: pd.DataFrame) -> list[tuple]:
    """Partition flight data into segments of TIMEOUT_INTERVAL_MS

    Args:
        FLIGHT_DATA (pd.DataFrame): Flight data with physics values. Sorted by time please

    Returns:
        not sure yet. A list of something
    """
    windows = []
    current_window = []
    group_start_time = None
    trailer_data = FLIGHT_DATA.iloc[0]  # The last packet in the last window

    for _, row in FLIGHT_DATA.iterrows():
        row_time_ms = row['# Time (s)'] * MS_PER_SECOND
        importance = packet_importance(row, trailer_data)

        if not current_window:
            # Start first window
            current_window.append((row, importance))
            group_start_time = row_time_ms
        else:
            # Check if current row exceeds group time window
            if row_time_ms <= group_start_time + TIMEOUT_INTERVAL_MS:
                current_window.append((row, importance))
            else:
                # Finalize current group and start new one
                windows.append(current_window)
                current_window = [(row, importance)]
                group_start_time = row_time_ms
                trailer_data = windows[-1][-1][0]

    # Add the final group if any rows remain
    if current_window:
        windows.append(current_window)

    return windows


def remove_extra_packets(flight_data) -> list:
    for i, window in enumerate(flight_data):
        # Pick the one with the highest importance
        flight_data[i] = max(window, key=lambda x: x[1])[0]
    return flight_data


def post_process_simulation_data(flight_data: pd.DataFrame) -> list:
    # Cull extra packets so there's only one packet per interval
    flight_data = flight_data.sort_values('# Time (s)').reset_index(drop=True)
    flight_data = partition_into_windows(flight_data)
    flight_data = remove_extra_packets(flight_data)
    return flight_data


def run_emulator(flight_data: pd.DataFrame, DEVICE_NAME: str):
    """
        Runs the emulator based on the flight data
        Uses a priority queue to organise which packets to send per interval
    """
    # Initialise mockpacket
    MockPacket.initialize_settings(
        config.load_config()['emulation'], FAKE_DEVICE_NAME=DEVICE_NAME)

    flight_data = post_process_simulation_data(flight_data)

    # Send the data to the mock packet
    start_time = time.monotonic()
    first_packet = True

    for packet in flight_data:
        PACKET_TIME_S = packet['# Time (s)']
        if (not first_packet):
            TIME_UNTIL_NEXT_PACKET_S = PACKET_TIME_S - \
                (last_packet_time - start_time)
            if TIME_UNTIL_NEXT_PACKET_S >= 0:
                time.sleep(TIME_UNTIL_NEXT_PACKET_S)
        else:
            first_packet = False
        if service_helper.time_to_stop():
            break
        send_simulated_packet(
            packet[" Altitude AGL (m)"],
            packet[" Speed - Velocity Magnitude (m/s)"],
            packet[" ω1 (rad/s)"],
            packet[" ω2 (rad/s)"],
            packet[" ω3 (rad/s)"],
            packet[" Ax (m/s²)"],
            packet[" Ay (m/s²)"],
            packet[" Az (m/s²)"]
        )
        last_packet_time = time.monotonic()


def validate_timeout_interval(TIMEOUT_MS):
    if TIMEOUT_MS < 0:
        slogger.error(f"Timeout interval cannot be negative: {TIMEOUT_MS}")
        raise ValueError("Timeout interval cannot be negative")
    if TIMEOUT_MS > 10000:
        slogger.warning(
            f"Timeout interval is quite large, consider reducing it: {TIMEOUT_MS}")


def main():
    slogger.info("Emulator Starting Simulation...")
    try:
        FAKE_DEVICE_PATH = sys.argv[sys.argv.index('--device-rocket') + 1]
    except ValueError:
        slogger.error(
            "Failed to find device names in arguments for simulator")
        raise
    FLIGHT_DATA = flight_simulation.get_simulated_flight_data()
    validate_timeout_interval(TIMEOUT_INTERVAL_MS)
    # Just to skip post processing if signal was recieved in data generation
    run_emulator(FLIGHT_DATA, FAKE_DEVICE_PATH)
    slogger.info("Simulation stopping")


if __name__ == "__main__":
    main()
