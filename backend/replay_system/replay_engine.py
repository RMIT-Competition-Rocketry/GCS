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
import config.config as config
from backend.tools.device_emulator import AVtoGCSData1, AVtoGCSData2, AVtoGCSData3, GSEtoGCSData1, GSEtoGCSData2, GCStoAVStateCMD, GCStoGSEStateCMD, MockPacket   
import backend.includes_python.process_logging as slogger
import backend.includes_python.service_helper as service_helper
import configparser

cfg = configparser.ConfigParser()
cfg.read("config/replay.ini")
timeout_cfg = cfg["Timeout"]
MIN_TIMESTAMP_MS = float(timeout_cfg["min_timeout_ms"])
SLEEP_BUFFER_MS = float(timeout_cfg["sleep_buffer_error"])

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
    
def process_csv_packets(min_timestamp_ms: int) -> List[Packet]:
    """Read and sort all the csv files"""
    packets = []
    for packet_type in PacketType:
        filename = f'backend/replay_system/mission_data/2025-05-04/{packet_type.name}.csv'
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    timestamp_ms = float(row['timestamp_ms'])
                    if timestamp_ms > min_timestamp_ms:
                        packet = Packet(
                            timestamp_ms= timestamp_ms,
                            packet_type = packet_type,
                            data = row
                        )
                        packets.append(packet)
        except FileNotFoundError:
            slogger.error(f'Warning Missing File: {filename}')
            
    return sorted(packets, key=lambda x : x.timestamp_ms)

def replay_packets(packets: List[Packet], min_timestamp_ms: int) -> None:
    if not packets:
        return 
    
    #first_timestamp = packets[0].timestamp_ms
    start_time = time.time() - (min_timestamp_ms / 1000)
    # last_status_time = start_time
    
    if service_helper.time_to_stop():
        return
    for packet in packets:
        if service_helper.time_to_stop():
            break
        # Find when the packet should be sent
        target_time = start_time + (packet.timestamp_ms) / 1000.0
        time_to_wait = target_time - time.time()
        if time_to_wait > 3.0:
            slogger.info(f"Time until next packet: {time_to_wait}")
        # slogger.debug(f"Time to wait: {time_to_wait} for packet: {packet.packet_type} at time: {packet.timestamp_ms}")
        if time_to_wait > 0:
            remaining_time = time_to_wait
            while remaining_time > 0:
                chunk = min(SLEEP_BUFFER_MS / 1000, time_to_wait)
                time.sleep(chunk)
                remaining_time -= chunk
                if service_helper.time_to_stop():
                    break
                
                
        if service_helper.time_to_stop():
            break
        
        # @TODO Progress Checkers
        # sent_time = time.time() + (MIN_TIMESTAMP_MS /1000) - start_time
        
        # current_time = time.time()
        # if current_time - last_status_time >= 60:
        #     if service_helper.time_to_stop():
        #         break
        #     elapsed = current_time - start_time
        #     packets_remaining = len(packets) - packets.index(packet) - 1
        #     slogger.debug(
        #         f"Status update: Elapsed {elapsed:.1f}s | "
        #         f"Packets remaining: {packets_remaining} | "
        #         f"Current packet: {packet.packet_type} @ {packet.timestamp_ms}ms"
        #     )
        #     last_status_time = current_time
            
        send_packet(packet)
        
def send_packet(packet: Packet) -> None:
    """Send packet based on the appropriate handler"""
    if service_helper.time_to_stop():
        return
    handler = PACKET_HANDLERS.get(packet.packet_type, unknown_packet_type)
    handler(packet)
       

def unknown_packet_type(packet: Packet) -> None:
    """Not a valid packet type"""
    slogger.error(f"Unknown packet type {packet.packet_type}")
    
def handle_av_to_gcs_data_1(packet: Packet) -> None:
    data = packet.data
    def temp_gyro_capper(packet: Packet, axis: str) -> Packet:
        gyro = "gyro_" + axis
        if float(data[gyro]) > 245:
            slogger.error(f"BAD GYRO {axis} ENTRY DETECTED CAPPING VALUE")
            data[gyro] = 245
        elif float(data[gyro]) < -245:
            slogger.error(f"BAD GYRO {axis} ENTRY DETECTED CAPPING VALUE")
            data[gyro] = -245
        return packet
    # Check gyro values
    packet = temp_gyro_capper(packet, "x")
    packet = temp_gyro_capper(packet, "y")
    packet = temp_gyro_capper(packet, "z")
    
    
    if service_helper.time_to_stop():
        return
    
    # Getting the flight state so its easier to convert into bits
    flight_state = int(data["FlightState"])
    item = AVtoGCSData1(
        RSSI = float(data["rssi"]),
        SNR = float(data["snr"]),
        FLIGHT_STATE_MSB=bool((flight_state >> 2) & 1),
        FLIGHT_STATE_1=bool((flight_state >> 1) & 1),
        FLIGHT_STATE_LSB=bool((flight_state >> 0) & 1),
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG= bool(data["dual_board_connectivity_state_flag"]),
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY= bool(data["recovery_checks_complete_and_flight_ready"]),
        GPS_FIX_FLAG= bool(data["GPS_fix_flag"]),
        PAYLOAD_CONNECTION_FLAG= bool(data["payload_connection_flag"]),
        CAMERA_CONTROLLER_CONNECTION = bool(data["camera_controller_connection_flag"]),
        ACCEL_LOW_X= int(float(data["accel_low_x"]) / 9.81 * 2048),
        ACCEL_LOW_Y= int(float(data["accel_low_y"]) / 9.81 * 2048),
        ACCEL_LOW_Z= int(float(data["accel_low_z"]) / 9.81 * 2048),
        ACCEL_HIGH_X= int(float(data['accel_high_x']) / 9.81 * -1048),
        ACCEL_HIGH_Y= int(float(data['accel_high_y']) / 9.81 * -1048),
        ACCEL_HIGH_Z= int(float(data['accel_high_z']) / 9.81 * 1048),
        GYRO_X=int((float(data["gyro_x"])) / 0.00875),
        GYRO_Y=int((float(data["gyro_y"])) / 0.00875),
        GYRO_Z=int((float(data["gyro_z"])) / 0.00875),
        ALTITUDE=float(data['altitude']),
        VELOCITY=float(data["velocity"]),
        APOGEE_PRIMARY_TEST_COMPETE=bool(data["apogee_primary_test_complete"]),
        APOGEE_SECONDARY_TEST_COMPETE=bool(data["apogee_secondary_test_complete"]),
        APOGEE_PRIMARY_TEST_RESULTS=bool(data["apogee_primary_test_results"]),
        APOGEE_SECONDARY_TEST_RESULTS=bool(data["apogee_secondary_test_results"]),
        MAIN_PRIMARY_TEST_COMPETE=bool(data["main_primary_test_complete"]),
        MAIN_SECONDARY_TEST_COMPETE=bool(data["main_secondary_test_complete"]),
        MAIN_PRIMARY_TEST_RESULTS=bool(data["main_primary_test_results"]),
        MAIN_SECONDARY_TEST_RESULTS=bool(data["main_secondary_test_results"]),
        MOVE_TO_BROADCAST=bool(data["broadcast_flag"])
    )
    item.write_payload()
    
def handle_av_to_gcs_data_2(packet: Packet) -> None:
    data = packet.data
    if service_helper.time_to_stop():
        return
    # Get flight state
    flight_state = int(data["FlightState"])
    item = AVtoGCSData2(
        RSSI = float(data["rssi"]),
        SNR= float(data['snr']),
        FLIGHT_STATE_MSB=bool((flight_state >> 2) & 1),
        FLIGHT_STATE_1=bool((flight_state >> 1) & 1),
        FLIGHT_STATE_LSB=bool((flight_state >> 0) & 1),
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG=bool(data['dual_board_connectivity_state_flag']),
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY=bool(data['recovery_checks_complete_and_flight_ready']),
        GPS_FIX_FLAG=bool(data['GPS_fix_flag']),
        PAYLOAD_CONNECTION_FLAG=bool(data["payload_connection_flag"]),
        CAMERA_CONTROLLER_CONNECTION=bool(data['camera_controller_connection_flag']),
        LATITUDE=float(data["GPS_latitude"]),
        LONGITUDE=float(data["GPS_longitude"]),
        QW=float(data['qw']),
        QX=float(data['qx']),
        QY=float(data['qy']),
        QZ=float(data['qz']),
    )
    item.write_payload()
    
def handle_av_to_gcs_data_3(packet: Packet) -> None:
    slogger.error("AV to GCS 3 not implemented")  

def handle_gse_to_gcs_data_1(packet: Packet) -> None:
    data = packet.data
    if service_helper.time_to_stop():
        return
    item = GSEtoGCSData1(
        RSSI=float(data["rssi"]),
        SNR=float(data["snr"]),
        MANUAL_PURGED=bool(data["manual_purge_activated"]),
        O2_FILL_ACTIVATED=bool(data["o2_fill_activated"]),
        SELECTOR_SWITCH_NEUTRAL_POSITION=bool(data["selector_switch_neutral_position"]),
        N2O_FILL_ACTIVATED=bool(data["n20_fill_activated"]),
        IGNITION_FIRED=bool(data["ignition_fired"]),
        IGNITION_SELECTED=bool(data["ignition_selected"]),
        GAS_FILL_SELECTED=bool(data["gas_fill_selected"]),
        SYSTEM_ACTIVATED=bool(data["system_activated"]),
        TRANSDUCER1=float(data["transducer_1"]),
        TRANSDUCER2=float(data["transducer_2"]),
        TRANSDUCER3=float(data["transducer_3"]),
        THERMOCOUPLE1=float(data["thermocouple_1"]),
        THERMOCOUPLE2=float(data["thermocouple_2"]),
        THERMOCOUPLE3=float(data["thermocouple_3"]),
        THERMOCOUPLE4=float(data["thermocouple_4"]),
        IGNITION_ERROR= bool(data["ignition_error"]),
        RELAY3_ERROR=bool(data["relay_3_error"]),
        RELAY2_ERROR=bool(data["relay_2_error"]),
        RELAY1_ERROR=bool(data["relay_1_error"]),
        THERMOCOUPLE_4_ERROR= bool(data["thermocouple_4_error"]),
        THERMOCOUPLE_3_ERROR=bool(data["thermocouple_3_error"]),
        THERMOCOUPLE_2_ERROR=bool(data["thermocouple_2_error"]),
        THERMOCOUPLE_1_ERROR=bool(data["thermocouple_1_error"]),
        LOAD_CELL_4_ERROR=bool(data["load_cell_4_error"]),
        LOAD_CELL_3_ERROR= bool(data["load_cell_3_error"]),
        LOAD_CELL_2_ERROR=bool(data["load_cell_2_error"]),
        LOAD_CELL_1_ERROR=bool(data["load_cell_1_error"]),
        TRANSDUCER_4_ERROR=bool(data["transducer_4_error"]),
        TRANSDUCER_3_ERROR=bool(data["transducer_3_error"]),
        TRANSDUCER_2_ERROR=bool(data["transducer_2_error"]),
        TRANSDUCER_1_ERROR=bool(data["transducer_1_error"])
    )
    item.write_payload()
        
def handle_gse_to_gcs_data_2(packet: Packet) -> None:
    data = packet.data
    if service_helper.time_to_stop():
        return
    item = GSEtoGCSData2(
        RSSI=float(data["rssi"]),
        SNR=float(data["snr"]),
        MANUAL_PURGED=bool(data["manual_purge_activated"]),
        O2_FILL_ACTIVATED=bool(data["o2_fill_activated"]),
        SELECTOR_SWITCH_NEUTRAL_POSITION=bool(data["selector_switch_neutral_position"]),
        N2O_FILL_ACTIVATED=bool(data["n20_fill_activated"]),
        IGNITION_FIRED=bool(data["ignition_fired"]),
        IGNITION_SELECTED=bool(data["ignition_selected"]),
        GAS_FILL_SELECTED=bool(data["gas_fill_selected"]),
        SYSTEM_ACTIVATED=bool(data["system_activated"]),
        INTERNAL_TEMPERATURE=float(data["internal_temp"]),
        WIND_SPEED=float(data["wind_speed"]),
        GAS_BOTTLE_WEIGHT_1=int(data["gas_bottle_weight_1"]),
        GAS_BOTTLE_WEIGHT_2=int(data["gas_bottle_weight_2"]),
        ADDITIONAL_VA_1=float(data["analog_voltage_input_1"]),
        ADDITIONAL_VA_2=float(data["analog_voltage_input_2"]),
        ADDITIONAL_CURRENT_1=float(data["additional_current_input_1"]),
        ADDITIONAL_CURRENT_2=float(data["additional_current_input_2"]),
        IGNITION_ERROR= bool(data["ignition_error"]),
        RELAY3_ERROR=bool(data["relay_3_error"]),
        RELAY2_ERROR=bool(data["relay_2_error"]),
        RELAY1_ERROR=bool(data["relay_1_error"]),
        THERMOCOUPLE_4_ERROR= bool(data["thermocouple_4_error"]),
        THERMOCOUPLE_3_ERROR=bool(data["thermocouple_3_error"]),
        THERMOCOUPLE_2_ERROR=bool(data["thermocouple_2_error"]),
        THERMOCOUPLE_1_ERROR=bool(data["thermocouple_1_error"]),
        LOAD_CELL_4_ERROR=bool(data["load_cell_4_error"]),
        LOAD_CELL_3_ERROR= bool(data["load_cell_3_error"]),
        LOAD_CELL_2_ERROR=bool(data["load_cell_2_error"]),
        LOAD_CELL_1_ERROR=bool(data["load_cell_1_error"]),
        TRANSDUCER_4_ERROR=bool(data["transducer_4_error"]),
        TRANSDUCER_3_ERROR=bool(data["transducer_3_error"]),
        TRANSDUCER_2_ERROR=bool(data["transducer_2_error"]),
        TRANSDUCER_1_ERROR=bool(data["transducer_1_error"])
    )
    item.write_payload()
    

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

def validate_timeout_skip(packet: Packet, min_timeout_ms: int) -> int:
    # Get the first packet timeout
    first_timestamp_ms = packet[0].timestamp_ms
    
    if (first_timestamp_ms > min_timeout_ms + SLEEP_BUFFER_MS):
        new_timeout = int(first_timestamp_ms - SLEEP_BUFFER_MS)
        slogger.warning(f"Minimum timeout is too long between packets, adjusting the min_timeout_ms to: {new_timeout}")
        return new_timeout
    return min_timeout_ms
    
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
    
    
    
    processed_packets = process_csv_packets(MIN_TIMESTAMP_MS)
    
    # Will need to valid timeout before the gaps between packets may be extremely large
    # When replaying the packets the delay will cause an error when trying to shut down
    valid_timeout = validate_timeout_skip(processed_packets, MIN_TIMESTAMP_MS)
 
    replay_packets(processed_packets, valid_timeout)
    slogger.info("FINISHED SENDING PACKETS")

if __name__ == "__main__":
    main()