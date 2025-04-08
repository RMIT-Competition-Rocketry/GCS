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
cfg.read("backend/simulation.ini")
sim_cfg = cfg["Simulation"]
TIMEOUT_INTERVAL = sim_cfg["timeout_interval"]
       
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
    
def isImportantPacket(current_row, last_row):
    if last_row is None:
        return True
    if current_row["flight_state"] != last_row["flight_state"]:
        return True
    
    # @TODO More important calculations

def run_emulator(flight_data: pd.Dataframe, device_name: str):
    # Init mockpacket
    #MockPacket.initialize_settings(config.load_config()['emulation'],FAKE_DEVICE_NAME=device_name,)
    
    # Getting the last few rows
    last_time = float('-inf')
    last_row = None
    
    # Filteration and sending packets
    for _, row in flight_data.iterrows():
        current_time = row["# Time(s)"]
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
    slogger.debug("Emulator Starting Simulation...")
   
    try:
        # @TODO PLEASE EDIT THIS DEVICE NAME ITS JUST COPIED STRAIGHT FROM EMULATOR
        DEVICE_NAME = sys.argv[sys.argv.index('--device-rocket') + 1]
        flight_data = flight_simulation.get_simulated_flight_data()
        run_emulator(flight_data, DEVICE_NAME)
    except Exception as e:
        sys.exit(1)
    

if __name__ == "__main__":
    main()