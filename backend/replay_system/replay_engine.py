"""
    Just read the csv file and read it linearly no stress
    Replay the following CSV files
    
"""
from enum import Enum
from dataclasses import dataclass
import csv
from typing import List
import time
from datetime import datetime
from backend.tools.device_emulator import AVtoGCSData1, AVtoGCSData2, AVtoGCSData3, GSEtoGCSData1, GSEtoGCSData2, GCStoAVStateCMD, GCStoGSEStateCMD    


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
    timestamp_ms: int
    packet_type = PacketType
    data = dict
    
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
                        timestamp_ms=int(row['timestamp_ms']),
                        packet_type = packet_type,
                        data = row
                    )
                    packets.append(packet)
        except FileNotFoundError:
            print(f'Warning Missing File: {filename}')
            
    return sorted(packets, key=lambda x : x.timestamp_ms)

def replay_packets(packets: List[Packet]) -> None:
    if not packets:
        return 
    
    start_time = time.time()
    first_timestamp = packets[0].timestamp_ms
    
    for packet in packets:
        # Find when the packet should be sent
        packet_delay = (packet.timestamp_ms - first_timestamp) / 1000.0
        elapsed_time = time.time() - start_time
        if elapsed_time < packet_delay:
            time.sleep(packet_delay - elapsed_time)
        
        send_packet(packet)
        
def send_packet(packet: Packet) -> None:
    """Send packet based on the appropriate handler"""
    handler = PACKET_HANDLERS.get(packet.packet_type, unknown_packet_type)
    handler(packet)
    
def unknown_packet_type(packet: Packet) -> None:
    """Not a valid packet type"""
    print(f"Unknown packet type {packet.packet_type}")
    
def handle_av_to_gcs_data_1(packet: Packet) -> None:
    data = packet["data"]
    for d in data:
        print(d)
    pass

def handle_av_to_gcs_data_2(packet: Packet) -> None:
    data = packet["data"]
    pass

def handle_av_to_gcs_data_3(packet: Packet) -> None:
    data = packet["data"]
    pass

def handle_gse_to_gcs_data_1(packet: Packet) -> None:
    data = packet["data"]
    pass

def handle_gse_to_gcs_data_2(packet: Packet) -> None:
    data = packet["data"]
    pass

def handle_gse_to_gcs_data_3(packet: Packet) -> None:
    data = packet["data"]
    pass

def handle_gse_to_gcs_data_3(packet: Packet) -> None:
    data = packet["data"]
    pass

def handle_gcs_to_av_state(packet: Packet) -> None:
    data = packet["data"]
    pass

def handle_gcs_to_gse_state(packet: Packet) -> None:
    data = packet["data"]
    pass

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
    
    
    




if __name__ == "__main__":
    processed_packets = process_csv_packets()
    replay_packets(processed_packets)