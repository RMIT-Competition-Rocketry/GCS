from rocket_sim import flight_simulation
from backend.tools.device_emulator import AVtoGCSData1, MockPacket
from itertools import count
import sys
import heapq
import pandas as pd
import backend.process_logging as slogger
import config.config as config
import configparser


# Setting up the config
cfg = configparser.ConfigParser()
cfg.read("config/simulation.ini")
sim_cfg = cfg["Simulation"]
# In seconds
TIMEOUT_INTERVAL = float(sim_cfg["timeout_interval"])
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
        MOVE_TO_BROADCAST=True
    )
    packet.write_payload()


def isImportantPacket(current_row, last_row):
    """
        Takes in two dataframe rows, this function simply determines if the 
        flight state is different indicating that its an important packet
    """
    # If its empty then the current row must be a new state ie important
    if last_row is None:
        return True

    if current_row["flight_state"] != last_row["flight_state"]:
        return True

    return False

    # @TODO More important calculations


def run_emulator(FLIGHT_DATA: pd.DataFrame, DEVICE_NAME: str):
    """
        Runs the emulator based on the flight data
        Uses a priority queue to organise which packets to send per interval
    """
    # Init mockpacket
    MockPacket.initialize_settings(
        config.load_config()['emulation'], FAKE_DEVICE_NAME=DEVICE_NAME)
    current_window_num = 0  # Start the timer at zero so we can track what timeframe window
    queue = []
    last_packet = None
    queue_num = count()  # For umabiguous heap ordering

    #  Refer to the TIMEOUT_INTEVAL as the window size
    for _, current_packet in FLIGHT_DATA.iterrows():
        # Convert the data frame to milliseconds, '# Time (s)' is the exact key in the df
        current_time = current_packet['# Time (s)'] * MS_PER_SECOND

        # Find out which window we are in to determine whether to create a new priority
        packet_window_num = int(current_time // TIMEOUT_INTERVAL)

        # If moved to a new window, then send previous window's packet
        while packet_window_num > current_window_num:
            # Process all the packets within this window frame
            if queue:
                _, _, packet = heapq.heappop(queue)
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
                last_packet = packet

            # Reset queue and move to next window
            current_window_num += 1
            queue = []

        # Prcoessing packets within timeframe
        # Calculating priority -1 for important 0 otherwise for max heap
        isImportant = isImportantPacket(current_packet, last_packet)
        priority = -1 if isImportant else 0

        # Add to current window's queue
        heapq.heappush(queue, (priority, next(queue_num), current_packet))

    # For the final packets
    if queue:
        _, _, packet = heapq.heappop(queue)
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
        # Empty the queue after
        queue = []


def main():
    slogger.info("Emulator Starting Simulation...")
    try:
        FAKE_DEVICE_PATH = sys.argv[sys.argv.index('--device-rocket') + 1]
    except ValueError:
        slogger.error(
            "Failed to find device names in arguments for simulator")
        raise
    FLIGHT_DATA = flight_simulation.get_simulated_flight_data()
    run_emulator(FLIGHT_DATA, FAKE_DEVICE_PATH)


if __name__ == "__main__":
    main()
