"""
    Just read the csv file and read it linearly no stress
    Replay the following CSV files
    
"""
from enum import Enum
from dataclasses import dataclass
import sys
import os
import csv
from typing import List
import time
from datetime import datetime
import config.config as config
from backend.tools.device_emulator import AVtoGCSData1, AVtoGCSData2, AVtoGCSData3, GSEtoGCSData1, GSEtoGCSData2, GCStoAVStateCMD, GCStoGSEStateCMD, MockPacket   
import backend.includes_python.process_logging as slogger
import backend.includes_python.service_helper as service_helper

class PacketType(Enum):
    GCS_TO_AV_STATE_CMD =  0
    GSE_TO_GCS_DATA_1 = 1
    GSE_TO_GCS_DATA_2 = 2
    GSE_TO_GCS_DATA_3 = 3 # Doesn't exist?
    AV_TO_GCS_DATA_1 = 4
    AV_TO_GCS_DATA_2 = 5
    AV_TO_GCS_DATA_3 = 6
    GCS_TO_GSE_STATE_CMD = 7

@dataclass
class Packet:
    timestamp_ms: float
    packet_type: PacketType
    data: dict
    
def process_csv_packets() -> List[Packet]:
    """Read and sort all the csv files"""
    packets = []
    for packet_type in PacketType:
        filename = f'backend/replay_system/mission_data/2025-05-04/{packet_type.name}.csv'
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    packet = Packet(
                        timestamp_ms= float(row['timestamp_ms']),
                        packet_type = packet_type,
                        data = row
                    )
                    packets.append(packet)
        except FileNotFoundError:
            slogger.error(f'Warning Missing File: {filename}')
            
    return sorted(packets, key=lambda x : x.timestamp_ms)

def replay_packets(packets: List[Packet]) -> None:
    if not packets:
        return 
    
    start_time = time.time()
    first_timestamp = packets[0].timestamp_ms
    total_time = 0
    if service_helper.time_to_stop():
        return
    for packet in packets:
        # Find when the packet should be sent
        
        target_time = start_time + (packet.timestamp_ms) / 1000.0
        time_to_wait = target_time - time.time()
        if time_to_wait > 0:
            time.sleep(time_to_wait)
        if service_helper.time_to_stop():
            break
        sent_time = time.time() - start_time
        #slogger.debug(f"Packet time: {str(packet.timestamp_ms)} Sent time: {str(sent_time * 1000)} for packet: {packet.packet_type}")
        send_packet(packet)
        
def send_packet(packet: Packet) -> None:
    """Send packet based on the appropriate handler"""
    handler = PACKET_HANDLERS.get(packet.packet_type, unknown_packet_type)
    handler(packet)
    
def unknown_packet_type(packet: Packet) -> None:
    """Not a valid packet type"""
    slogger.error(f"Unknown packet type {packet.packet_type}")
    
def handle_av_to_gcs_data_1(packet: Packet) -> None:
    data = packet.data
    item = AVtoGCSData1(
        RSSI = data.get["rssi"],
        SNR = data.get["snr"],
        FLIGHT_STATE_MSB=False,
        FLIGHT_STATE_1=False,
        FLIGHT_STATE_LSB=False,
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG= data.get["dual_board_connectivity_state_flag"],
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY= data.get["recovery_checks_complete_and_flight_ready"],
        GPS_FIX_FLAG= data.get["GPS_fix_flag"],
        PAYLOAD_CONNECTION_FLAG= data.get["payload_connection_flag"],
        CAMERA_CONTROLLER_CONNECTION = data.get["camera_controller_connection_flag"],
        ACCEL_LOW_X= data.get["accel_low_x"],
        ACCEL_LOW_Y= data.get["accel_low_y"],
        ACCEL_LOW_Z= data.get["accel_low_z"],
        ACCEL_HIGH_X= data.get['accel_high_x'],
        ACCEL_HIGH_Y= data.get['accel_high_y'],
        ACCEL_HIGH_Z= data.get['accel_high_z'],
        GYRO_X=data.get["gyro_x"],
        GYRO_Y=data.get["gyro_y"],
        GYRO_Z=data.get["gyro_z"],
        ALTITUDE=data.get['altitude'],
        VELOCITY=data.get["velocity"],
        APOGEE_PRIMARY_TEST_COMPETE=data.get["apogee_primary_test_complete"],
        APOGEE_SECONDARY_TEST_COMPETE=data.get["apogee_secondary_test_complete"],
        APOGEE_PRIMARY_TEST_RESULTS=data.get["apogee_primary_test_results"],
        APOGEE_SECONDARY_TEST_RESULTS=data.get["apogee_secondary_test_results"],
        MAIN_PRIMARY_TEST_COMPETE=data.get["main_primary_test_complete"],
        MAIN_SECONDARY_TEST_COMPETE=data.get["main_secondary_test_complete"],
        MAIN_PRIMARY_TEST_RESULTS=data.get["main_primary_test_results"],
        MAIN_SECONDARY_TEST_RESULTS=data.get["main_secondary_test_results"],
        MOVE_TO_BROADCAST=data.get["broadcast_flag"]
    )
    item.write_payload()
    
    

def handle_av_to_gcs_data_2(packet: Packet) -> None:
    data = packet.data
    item = AVtoGCSData2(
        RSSI = data.get["rssi"],
        SNR= data.get['snr'],
        FLIGHT_STATE_MSB=False,
        FLIGHT_STATE_1=False,
        FLIGHT_STATE_LSB=False,
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG=data.get['dual_board_connectivity_state_flag'],
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY=data.get['recovery_checks_complete_and_flight_ready'],
        GPS_FIX_FLAG=data.get['GPS_fix_flag'],
        PAYLOAD_CONNECTION_FLAG=data.get["payload_connection_flag"],
        CAMERA_CONTROLLER_CONNECTION=data.get['camera_controller_connection_flag'],
        LATITUDE=data.get["GPS_latitude"],
        LONGITUDE=data.get["GPS_longitude"],
        QW=data.get['qw'],
        QX=data.get['qx'],
        QY=data.get['qy'],
        QZ=data.get['qz'],
    )
    
    

def handle_av_to_gcs_data_3(packet: Packet) -> None:
    slogger.error("AV to GCS 3 not implemented")
    
    

def handle_gse_to_gcs_data_1(packet: Packet) -> None:
    data = packet.data
    item = GSEtoGCSData1(
        RSSI=data.get("rssi"),
        SNR=data.get("snr"),
        MANUAL_PURGED=data.get("manual_purged"),
        O2_FILL_ACTIVATED=data.get("o2_fill_activated"),
        SELECTOR_SWITCH_NEUTRAL_POSITION=data.get("selector_switch_neutral_position"),
        N2O_FILL_ACTIVATED=data.get("n2o_fill_activated"),
        IGNITION_FIRED=data.get("ignition_fired"),
        IGNITION_SELECTED=data.get("ignition_selected"),
        GAS_FILL_SELECTED=data.get("gas_fill_selected"),
        SYSTEM_ACTIVATED=data.get("system_activated"),
        TRANSDUCER1=data.get("transducer_1"),
        TRANSDUCER2=data.get("transducer_2"),
        TRANSDUCER3=data.get("transducer_3"),
        THERMOCOUPLE1=data.get("thermocouple_1"),
        THERMOCOUPLE2=data.get("thermocouple_2"),
        THERMOCOUPLE3=data.get("thermocouple_3"),
        THERMOCOUPLE4=data.get("thermocouple_4"),
        IGNITION_ERROR=data.get("ignition_error"),
        RELAY3_ERROR=data.get("relay_3_error"),
        RELAY2_ERROR=data.get("relay_2_error"),
        RELAY1_ERROR=data.get("relay_1_error"),
        THERMOCOUPLE_4_ERROR=data.get("thermocouple_4_error"),
        THERMOCOUPLE_3_ERROR=data.get("thermocouple_3_error"),
        THERMOCOUPLE_2_ERROR=data.get("thermocouple_2_error"),
        THERMOCOUPLE_1_ERROR=data.get("thermocouple_1_error"),
        LOAD_CELL_4_ERROR=data.get("load_cell_4_error"),
        LOAD_CELL_3_ERROR=data.get("load_cell_3_error"),
        LOAD_CELL_2_ERROR=data.get("load_cell_2_error"),
        LOAD_CELL_1_ERROR=data.get("load_cell_1_error"),
        TRANSDUCER_4_ERROR=data.get("transducer_4_error"),
        TRANSDUCER_3_ERROR=data.get("transducer_3_error"),
        TRANSDUCER_2_ERROR=data.get("transducer_2_error"),
        TRANSDUCER_1_ERROR=data.get("transducer_1_error")
    )
        
    
    

def handle_gse_to_gcs_data_2(packet: Packet) -> None:
    data = packet.data
    

def handle_gse_to_gcs_data_3(packet: Packet) -> None:
    slogger.error("GSE to GCS 3 not implemented")
    

def handle_gcs_to_av_state(packet: Packet) -> None:
    slogger.error("GCS to AV State not implemented")
    

def handle_gcs_to_gse_state(packet: Packet) -> None:
    slogger.error("GCS to GSE state not implemented")
    
def get_available_missions() -> List[str]:
    dir = "backend/replay_system/mission_data"
    return [d for d in os.listdir(dir) if os.path.isdir(os.path.join(dir, d))]
    

PACKET_HANDLERS = {
    PacketType.AV_TO_GCS_DATA_1: handle_av_to_gcs_data_1,
    PacketType.AV_TO_GCS_DATA_2: handle_av_to_gcs_data_2,
    PacketType.AV_TO_GCS_DATA_3: handle_av_to_gcs_data_3,
    PacketType.GCS_TO_AV_STATE_CMD: handle_gcs_to_av_state,
    PacketType.GSE_TO_GCS_DATA_1: handle_gse_to_gcs_data_1,
    PacketType.GSE_TO_GCS_DATA_2: handle_gse_to_gcs_data_2,
    PacketType.GSE_TO_GCS_DATA_2: handle_gse_to_gcs_data_2,
    PacketType.GCS_TO_GSE_STATE_CMD: handle_gcs_to_gse_state, 
}
    
    
def main():
    available_mission_data = get_available_missions()
    if not available_mission_data:
        slogger.error("No mission data in the directory backend/replay_system/mission_data")
        
    # Only one mission data @TODO please make it based on args
    mission = available_mission_data[-1]
    slogger.info(f"Available missions: {','.join(available_mission_data)}")
    slogger.info(f"Emulator Starting Replay System from mission {mission}")
    try:
        FAKE_DEVICE_PATH = sys.argv[sys.argv.index('--device-rocket') + 1]
        MockPacket.initialize_settings(
        config.load_config()['emulation'], FAKE_DEVICE_NAME=FAKE_DEVICE_PATH
    )
    except ValueError:
        slogger.error("Failed to find device names in arguments for replay system")
        raise
    
    
    processed_packets = process_csv_packets()
    replay_packets(processed_packets)




if __name__ == "__main__":
    main()