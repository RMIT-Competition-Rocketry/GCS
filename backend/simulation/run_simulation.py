from rocket_sim import flight_simulation
from backend.tools.device_emulator import AVtoGCSData1, MockPacket
import pandas as pd
import time

def send_simulated_packet(altitude: float, speed: float, w1: float, w2: float, w3: float, ax: float, ay: float, az: float):
    packet = AVtoGCSData1(
        FLIGHT_STATE_MSB=False,
        FLIGHT_STATE_1=False,
        FLIGHT_STATE_LSB=False,
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG=False,
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY=False,
        GPS_FIX_FLAG=False,
        PAYLOAD_CONNECTION_FLAG=True,
        CAMERA_CONTROLLER_CONNECTION=True,
        ACCEL_LOW_X=2048*ax,
        ACCEL_LOW_Y=ay * 2048,
        ACCEL_LOW_Z=az * 2048,
        ACCEL_HIGH_X=ax * 2048,
        ACCEL_HIGH_Y=ay * 2048,
        ACCEL_HIGH_Z=ay * 2048,
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

def main():
    # This should give a pandas dataframe
    flight_data = flight_simulation.get_simulated_flight_data()
    
    # Time to push to the real function
    # columns = [
    # "# Time (s)",
    # " Altitude AGL (m)",
    # " Speed - Velocity Magnitude (m/s)",
    # " ω1 (rad/s)",
    # " ω2 (rad/s)",
    # " ω3 (rad/s)",
    # " Ax (m/s²)",
    # " Ay (m/s²)",
    # " Az (m/s²)"
    # ]
    timeout = 0.01
    for idx, row in flight_data.iterrows():
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
        time.sleep(timeout)

    
    
    
if __name__ == "__main__":
    main()