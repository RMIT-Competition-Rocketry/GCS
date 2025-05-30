from backend.simulation.rocket_sim import flight_simulation
from backend.device_emulator import AVtoGCSData1, AVtoGCSData2, MockPacket
from itertools import count
from enum import Enum
import numpy as np
import os
import math
import sys
import pandas as pd
import time
import backend.includes_python.process_logging as slogger
import backend.includes_python.service_helper as service_helper
import config.config as config
import configparser
from backend.replay_system.replay_engine import Packet
from backend.replay_system.packet_type import PacketType

# Setting up enum

# Setting up the config
cfg = configparser.ConfigParser()
cfg.read("config/simulation.ini")
sim_cfg = cfg["Simulation"]
# In seconds
TIMEOUT_INTERVAL_MS = float(sim_cfg["timeout_interval_ms"])
MS_PER_SECOND = 1000


def send_simulated_packet(altitude: float, speed: float, w1: float, w2: float, w3: float, ax: float, ay: float, az: float, latitude: float, longitude: float, qw: float, qx: float, qy: float, qz: float, qm: float):
    """
    Sends a simulated telemetry packet with the provided sensor values.

    Parameters:
    - altitude (float): Altitude of the rocket in meters.
    - speed (float): Speed of the rocket in meters per second.
    - w1, w2, w3 (float): Angular velocity readings (typically from a gyroscope).
      These should be divided by 0.00875 to convert to degrees per second.
    - ax, ay, az (float): Acceleration readings (typically from an accelerometer).
      These should be converted from m/s^2 to g-force units (divide by 9.80665).
    - Latitude, Longitude (float): this is the coordinates of the rocket at time t
    - qw, qx, qy, qz (float): quaternions
    - qm (float): the magnitude of all the quaternion components

    Notes:
    - The conversion is currently being done in this function so don't worry about that
    - The packet format and transmission method should match the backend
    """
    packet1 = AVtoGCSData1(
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
        MOVE_TO_BROADCAST=True
    )
    packet2 = AVtoGCSData2(
        LATITUDE=latitude,
        LONGITUDE=longitude,
        QW=qw / abs(qm),
        QX=qx / abs(qm),
        QY=qy / abs(qm),
        QZ=qz / abs(qm)
    )
    # https://github.com/RMIT-Competition-Rocketry/GCS/issues/114
    if service_helper.time_to_stop():
        return
    packet1.write_payload()
    packet2.write_payload()


def packet_importance(PACKET, PREVIOUS_WINDOW_TRAILER) -> int:
    """
        Returns a numerical score on how 'important' the packet is
        We don't want to drop these packets

        Args:
            PACKET (type): Current packet for observation
            PREVIOUS_WINDOW_TRAILER (type): Last packet in previous window
    """
    importance = 0
    if PREVIOUS_WINDOW_TRAILER is None:
        return importance + 1
    last_window_state = PREVIOUS_WINDOW_TRAILER["flight_state"]
    current_packet_state = PACKET["flight_state"]

    # Increase score if this packet has a different flight state than last window
    if last_window_state is None or last_window_state != current_packet_state:
        importance += 1

    return importance


def partition_into_windows(FLIGHT_DATA: pd.DataFrame) -> list[tuple]:
    """Partition flight data into segments of TIMEOUT_INTERVAL

    Args:
        FLIGHT_DATA (pd.DataFrame): Flight data with physics values. Sorted by time please

    Returns:
        not sure yet. A list of something
    """
    windows = []
    current_window = []
    group_start_time = None
    trailer_data = None  # The last packet in the last window

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
                trailer_data = windows[-1][-1][0] if windows else None
                current_window = [(row, packet_importance(row, trailer_data))]
                group_start_time = row_time_ms

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
    flight_data = inject_data(flight_data)
    flight_data = partition_into_windows(flight_data)
    flight_data = remove_extra_packets(flight_data)
    return flight_data


def inject_data(flight_data: pd.DataFrame) -> pd.DataFrame:
    INJECTION_DELAY_S = 10.0
    SAMPLING_RATE_S = 0.01

    # Shift all timestamps by the injection delay
    flight_data["# Time (s)"] = flight_data["# Time (s)"] + INJECTION_DELAY_S

    # Get the first row's data (excluding time column)
    first_data = flight_data.iloc[0, 1:].to_dict()

    start_time = 0
    end_time = start_time + INJECTION_DELAY_S
    new_times = np.arange(start_time, end_time, SAMPLING_RATE_S)

    # Create new rows with repeated first data point
    new_rows = []
    for t in new_times:
        new_row = {"# Time (s)": float(round(t, 2))}
        new_row.update(first_data)
        new_rows.append(new_row)

    # Create DataFrame from the new rows
    injected_data = pd.DataFrame(new_rows)

    flight_data = pd.concat([flight_data, injected_data]
                            ).sort_values("# Time (s)")
    flight_data["# Time (s)"] = flight_data['# Time (s)']
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
    first_packet = True
    START_TIME = time.monotonic()

    def _time_until_next_packet_s(PACKET_TIME_S):
        return PACKET_TIME_S - (time.monotonic() - START_TIME)

    for packet in flight_data:
        PACKET_TIME_S = packet['# Time (s)']
        if (not first_packet):
            time_until_next_packet_s = _time_until_next_packet_s(PACKET_TIME_S)
            if time_until_next_packet_s > 0.6:
                time.sleep(time_until_next_packet_s*0.8)  # sleep off 80% of it
            while _time_until_next_packet_s(PACKET_TIME_S) > 0:
                pass  # Busy wait to avoid sub 20-50ms sleep inaccuracies

        else:
            first_packet = False
        if service_helper.time_to_stop():
            break
        qw = packet[" e0"]
        qx = packet[" e1"]
        qy = packet[" e2"]
        qz = packet[" e3"]
        # Using qm to normalize the quaternions to [-1,1]
        qm = math.sqrt(qw**2 + qx**2 + qy**2 + qz**2)
        send_simulated_packet(
            packet[" Altitude AGL (m)"],
            packet[" Speed - Velocity Magnitude (m/s)"],
            packet[" ω1 (rad/s)"],
            packet[" ω2 (rad/s)"],
            packet[" ω3 (rad/s)"],
            packet[" Ax (m/s²)"],
            packet[" Ay (m/s²)"],
            packet[" Az (m/s²)"],
            packet[" Latitude (°)"],
            packet[" Longitude (°)"],
            packet[" e0"],
            packet[" e1"],
            packet[" e2"],
            packet[" e3"],
            qm,
        )


def simulation_to_replay_data(flight_data: pd.DataFrame):
    """Convert to the Packet data struct"""
    # Need to seperate data into seperate packets
    packets = []

    for packet in flight_data:
        # Need to normalise quaternions for AV2, this shouldnt be too much of an issue because we have to call it for every function anyways
        qw = packet[" e0"]
        qx = packet[" e1"]
        qy = packet[" e2"]
        qz = packet[" e3"]
        # Using qm to normalize the quaternions to [-1,1]
        qm = abs(math.sqrt(qw**2 + qx**2 + qy**2 + qz**2))
        AV1_PACKET = Packet(
            timestamp_ms=float(packet["# Time (s)"]) * 1000,
            packet_type=PacketType.AV_TO_GCS_DATA_1,
            data={
                "rssi": 0,
                "snr": 69.0,
                "FlightState": int(packet["flight_state"]),
                "dual_board_connectivity_state_flag": False,
                "recovery_checks_complete_and_flight_ready": False,
                "GPS_fix_flag": False,
                "payload_connection_flag": False,
                "camera_controller_connection_flag": False,
                "accel_low_x": float(packet[" Ax (m/s²)"]),
                "accel_low_y": float(packet[" Ay (m/s²)"]),
                "accel_low_z": float(packet[" Az (m/s²)"]),
                "accel_high_x": float(packet[" Ax (m/s²)"]),
                "accel_high_y": float(packet[" Ay (m/s²)"]),
                "accel_high_z": float(packet[" Az (m/s²)"]),
                "gyro_x": float(packet[" ω1 (rad/s)"]),
                "gyro_y": float(packet[" ω2 (rad/s)"]),
                "gyro_z": float(packet[" ω3 (rad/s)"]),
                "altitude": float(packet[" Altitude AGL (m)"]),
                "velocity": float(packet[" Speed - Velocity Magnitude (m/s)"]),
                "apogee_primary_test_complete": False,
                "apogee_secondary_test_complete": False,
                "apogee_primary_test_results": False,
                "apogee_secondary_test_results": False,
                "main_primary_test_complete": False,
                "main_secondary_test_complete": False,
                "main_primary_test_results": False,
                "main_secondary_test_results": False,
                "broadcast_flag": True
            }
        )
        packets.append(AV1_PACKET)
        AV2_PACKET = Packet(
            timestamp_ms=packet['# Time (s)'] * 1000,
            packet_type=PacketType.AV_TO_GCS_DATA_2,
            data={
                "rssi": 0,
                "snr": 69.0,
                "FlightState": int(packet["flight_state"]),
                "dual_board_connectivity_state_flag": False,
                "recovery_checks_complete_and_flight_ready": False,
                "GPS_fix_flag": False,
                "payload_connection_flag": False,
                "camera_controller_connection_flag": False,
                "GPS_latitude": float(packet[" Latitude (°)"]),
                "GPS_longitude": float(packet[" Longitude (°)"]),
                "qw": float(qw),
                "qx": float(qx),
                "qy": float(qy),
                "qz": float(qz)
            }
        )
        packets.append(AV2_PACKET)

    return packets


# @TODO Super unsafe lol
def get_replay_sim_data():
    """flightType enum will be used later on when rebuilding the sim for now its just an unused variable"""
    FLIGHT_DATA = flight_simulation.get_simulated_flight_data()
    processed_data = post_process_simulation_data(FLIGHT_DATA)

    replay_processed = simulation_to_replay_data(processed_data)

    return replay_processed


def main():
    slogger.info("Emulator Starting Simulation...")
    try:
        FAKE_DEVICE_PATH = sys.argv[sys.argv.index('--device-rocket') + 1]
    except ValueError:
        slogger.error("Failed to find device names in arguments for simulator")
        raise
    FLIGHT_DATA = flight_simulation.get_simulated_flight_data()
    run_emulator(FLIGHT_DATA, FAKE_DEVICE_PATH)


if __name__ == "__main__":
    main()
