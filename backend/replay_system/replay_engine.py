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
from backend.device_emulator import AVtoGCSData1, AVtoGCSData2, AVtoGCSData3, GSEtoGCSData1, GSEtoGCSData2, GCStoAVStateCMD, GCStoGSEStateCMD, MockPacket
import backend.includes_python.process_logging as slogger
import backend.includes_python.service_helper as service_helper
from backend.replay_system.packet_type import PacketType
import configparser
import argparse

cfg = configparser.ConfigParser()
cfg.read("config/replay.ini")
timeout_cfg = cfg["Timeout"]
MIN_TIMESTAMP_MS = float(timeout_cfg["min_timeout_ms"])
SLEEP_BUFFER_MS = float(timeout_cfg["sleep_buffer_error"])


@dataclass
class Packet:
    timestamp_ms: float
    packet_type: PacketType
    data: dict


def process_csv_packets(min_timestamp_ms: int, mission_path: str) -> List[Packet]:
    """Read and sort all the csv files"""
    packets = []
    for packet_type in PacketType:

        filename = os.path.join(mission_path, f"{packet_type.name}.csv")
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    timestamp_ms = float(row['timestamp_ms'])
                    if timestamp_ms > min_timestamp_ms:
                        packet = Packet(
                            timestamp_ms=timestamp_ms,
                            packet_type=packet_type,
                            data=row
                        )
                        packets.append(packet)
        except FileNotFoundError:
            slogger.error(f'Warning Missing File: {filename}')

    return sorted(packets, key=lambda x: x.timestamp_ms)


def replay_packets(packets: List[Packet], min_timestamp_ms: int) -> None:
    if not packets:
        return

    # first_timestamp = packets[0].timestamp_ms
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
        if time_to_wait >= 3.0:
            slogger.warning(
                f"Time until next packet: {round(time_to_wait,3)} seconds")
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
    time.sleep(0.01)
    handle_packets(packet)


def handle_packets(packet: Packet):
    match packet.packet_type:
        case PacketType.AV_TO_GCS_DATA_1:
            _handle_av_to_gcs_data_1(packet)
        case PacketType.AV_TO_GCS_DATA_2:
            _handle_av_to_gcs_data_2(packet)
        case PacketType.AV_TO_GCS_DATA_3:
            _handle_av_to_gcs_data_3(packet)
        case PacketType.GCS_TO_AV_STATE_CMD:
            _handle_gcs_to_av_state(packet)
        case PacketType.GSE_TO_GCS_DATA_1:
            _handle_gse_to_gcs_data_1(packet)
        case PacketType.GSE_TO_GCS_DATA_2:
            _handle_gse_to_gcs_data_2(packet)
        case PacketType.GSE_TO_GCS_DATA_3:
            _handle_gse_to_gcs_data_3(packet)
        case PacketType.GCS_TO_GSE_STATE_CMD:
            _handle_gcs_to_gse_state(packet)
        case _:
            _unknown_packet_type


def _unknown_packet_type(packet: Packet) -> None:
    """Not a valid packet type"""
    slogger.error(f"Unknown packet type {packet.packet_type}")
    raise ValueError


def _handle_av_to_gcs_data_1(packet: Packet) -> None:
    data = packet.data

    def _gyro_capper(packet: Packet, axis: str) -> Packet:
        key = "gyro_" + axis
        CURRENT_VALUE = float(data[key])

        ABS_THRESHOLD = 245.0

        if CURRENT_VALUE > ABS_THRESHOLD:
            slogger.error(
                f"BAD {key.upper()}={CURRENT_VALUE} ENTRY DETECTED CAPPING VALUE")
            data[key] = ABS_THRESHOLD
        elif CURRENT_VALUE < -ABS_THRESHOLD:
            slogger.error(
                f"BAD {key.upper()}={CURRENT_VALUE} ENTRY DETECTED CAPPING VALUE")
            data[key] = -ABS_THRESHOLD
        return packet
    # Check gyro values
    packet = _gyro_capper(packet, "x")
    packet = _gyro_capper(packet, "y")
    packet = _gyro_capper(packet, "z")

    if service_helper.time_to_stop():
        return

    # Getting the flight state so its easier to convert into bits
    flight_state = int(data["FlightState"])
    item = AVtoGCSData1(
        RSSI=float(data["rssi"]),
        SNR=float(data["snr"]),
        FLIGHT_STATE_=flight_state,
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG=bool(
            data["dual_board_connectivity_state_flag"]),
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY=bool(
            data["recovery_checks_complete_and_flight_ready"]),
        GPS_FIX_FLAG=bool(data["GPS_fix_flag"]),
        PAYLOAD_CONNECTION_FLAG=bool(data["payload_connection_flag"]),
        CAMERA_CONTROLLER_CONNECTION=bool(
            data["camera_controller_connection_flag"]),
        ACCEL_LOW_X=int(float(data["accel_low_x"]) / 9.81 * 2048),
        ACCEL_LOW_Y=int(float(data["accel_low_y"]) / 9.81 * 2048),
        ACCEL_LOW_Z=int(float(data["accel_low_z"]) / 9.81 * 2048),
        ACCEL_HIGH_X=int(float(data['accel_high_x']) / 9.81 * -1048),
        ACCEL_HIGH_Y=int(float(data['accel_high_y']) / 9.81 * -1048),
        ACCEL_HIGH_Z=int(float(data['accel_high_z']) / 9.81 * 1048),
        GYRO_X=int((float(data["gyro_x"])) / 0.00875),
        GYRO_Y=int((float(data["gyro_y"])) / 0.00875),
        GYRO_Z=int((float(data["gyro_z"])) / 0.00875),
        ALTITUDE=float(data['altitude']),
        VELOCITY=float(data["velocity"]),
        APOGEE_PRIMARY_TEST_COMPETE=bool(data["apogee_primary_test_complete"]),
        APOGEE_SECONDARY_TEST_COMPETE=bool(
            data["apogee_secondary_test_complete"]),
        APOGEE_PRIMARY_TEST_RESULTS=bool(data["apogee_primary_test_results"]),
        APOGEE_SECONDARY_TEST_RESULTS=bool(
            data["apogee_secondary_test_results"]),
        MAIN_PRIMARY_TEST_COMPETE=bool(data["main_primary_test_complete"]),
        MAIN_SECONDARY_TEST_COMPETE=bool(data["main_secondary_test_complete"]),
        MAIN_PRIMARY_TEST_RESULTS=bool(data["main_primary_test_results"]),
        MAIN_SECONDARY_TEST_RESULTS=bool(data["main_secondary_test_results"]),
        MOVE_TO_BROADCAST=bool(data["broadcast_flag"])
    )
    item.write_payload()


def _handle_av_to_gcs_data_2(packet: Packet) -> None:
    data = packet.data
    if service_helper.time_to_stop():
        return
    # Get flight state
    flight_state = int(data["FlightState"])
    item = AVtoGCSData2(
        RSSI=float(data["rssi"]),
        SNR=float(data['snr']),
        FLIGHT_STATE_=flight_state,
        DUAL_BOARD_CONNECTIVITY_STATE_FLAG=bool(
            data['dual_board_connectivity_state_flag']),
        RECOVERY_CHECK_COMPLETE_AND_FLIGHT_READY=bool(
            data['recovery_checks_complete_and_flight_ready']),
        GPS_FIX_FLAG=bool(data['GPS_fix_flag']),
        PAYLOAD_CONNECTION_FLAG=bool(data["payload_connection_flag"]),
        CAMERA_CONTROLLER_CONNECTION=bool(
            data['camera_controller_connection_flag']),
        LATITUDE=float(data["GPS_latitude"]),
        LONGITUDE=float(data["GPS_longitude"]),
        QW=float(data['qw']),
        QX=float(data['qx']),
        QY=float(data['qy']),
        QZ=float(data['qz']),
    )
    item.write_payload()


def _handle_av_to_gcs_data_3(packet: Packet) -> None:
    slogger.error("AV to GCS 3 not implemented")


def _handle_gse_to_gcs_data_1(packet: Packet) -> None:
    data = packet.data
    if service_helper.time_to_stop():
        return
    item = GSEtoGCSData1(
        RSSI=float(data["rssi"]),
        SNR=float(data["snr"]),
        MANUAL_PURGED=bool(data["manual_purge_activated"]),
        O2_FILL_ACTIVATED=bool(data["o2_fill_activated"]),
        SELECTOR_SWITCH_NEUTRAL_POSITION=bool(
            data["selector_switch_neutral_position"]),
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
        IGNITION_ERROR=bool(data["ignition_error"]),
        RELAY3_ERROR=bool(data["relay_3_error"]),
        RELAY2_ERROR=bool(data["relay_2_error"]),
        RELAY1_ERROR=bool(data["relay_1_error"]),
        THERMOCOUPLE_4_ERROR=bool(data["thermocouple_4_error"]),
        THERMOCOUPLE_3_ERROR=bool(data["thermocouple_3_error"]),
        THERMOCOUPLE_2_ERROR=bool(data["thermocouple_2_error"]),
        THERMOCOUPLE_1_ERROR=bool(data["thermocouple_1_error"]),
        LOAD_CELL_4_ERROR=bool(data["load_cell_4_error"]),
        LOAD_CELL_3_ERROR=bool(data["load_cell_3_error"]),
        LOAD_CELL_2_ERROR=bool(data["load_cell_2_error"]),
        LOAD_CELL_1_ERROR=bool(data["load_cell_1_error"]),
        TRANSDUCER_4_ERROR=bool(data["transducer_4_error"]),
        TRANSDUCER_3_ERROR=bool(data["transducer_3_error"]),
        TRANSDUCER_2_ERROR=bool(data["transducer_2_error"]),
        TRANSDUCER_1_ERROR=bool(data["transducer_1_error"])
    )
    item.write_payload()


def _handle_gse_to_gcs_data_2(packet: Packet) -> None:
    data = packet.data
    if service_helper.time_to_stop():
        return
    item = GSEtoGCSData2(
        RSSI=float(data["rssi"]),
        SNR=float(data["snr"]),
        MANUAL_PURGED=bool(data["manual_purge_activated"]),
        O2_FILL_ACTIVATED=bool(data["o2_fill_activated"]),
        SELECTOR_SWITCH_NEUTRAL_POSITION=bool(
            data["selector_switch_neutral_position"]),
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
        IGNITION_ERROR=bool(data["ignition_error"]),
        RELAY3_ERROR=bool(data["relay_3_error"]),
        RELAY2_ERROR=bool(data["relay_2_error"]),
        RELAY1_ERROR=bool(data["relay_1_error"]),
        THERMOCOUPLE_4_ERROR=bool(data["thermocouple_4_error"]),
        THERMOCOUPLE_3_ERROR=bool(data["thermocouple_3_error"]),
        THERMOCOUPLE_2_ERROR=bool(data["thermocouple_2_error"]),
        THERMOCOUPLE_1_ERROR=bool(data["thermocouple_1_error"]),
        LOAD_CELL_4_ERROR=bool(data["load_cell_4_error"]),
        LOAD_CELL_3_ERROR=bool(data["load_cell_3_error"]),
        LOAD_CELL_2_ERROR=bool(data["load_cell_2_error"]),
        LOAD_CELL_1_ERROR=bool(data["load_cell_1_error"]),
        TRANSDUCER_4_ERROR=bool(data["transducer_4_error"]),
        TRANSDUCER_3_ERROR=bool(data["transducer_3_error"]),
        TRANSDUCER_2_ERROR=bool(data["transducer_2_error"]),
        TRANSDUCER_1_ERROR=bool(data["transducer_1_error"])
    )
    item.write_payload()


def _handle_gse_to_gcs_data_3(packet: Packet) -> None:
    slogger.error("GSE to GCS 3 not implemented")


def _handle_gcs_to_av_state(packet: Packet) -> None:
    slogger.error("GCS to AV State not implemented")


def _handle_gcs_to_gse_state(packet: Packet) -> None:
    slogger.error("GCS to GSE state not implemented")


def validate_timeout_skip(packet: Packet, min_timeout_ms: int) -> int:
    # Get the first packet timeout
    first_timestamp_ms = packet[0].timestamp_ms

    if (first_timestamp_ms > min_timeout_ms + SLEEP_BUFFER_MS):
        new_timeout = int(first_timestamp_ms - SLEEP_BUFFER_MS)
        slogger.warning(
            f"Minimum timeout is too long between packets, adjusting the min_timeout_ms to: {new_timeout}")
        return new_timeout
    return min_timeout_ms


def get_mission_path():
    base_path = os.path.join("backend", "replay_system", "mission_data")
    return base_path


def main():
    # Using parser because theres too many arguments and I couldn't get sys working
    parser = argparse.ArgumentParser()
    parser.add_argument('--device-rocket', required=True)
    parser.add_argument(
        '--mode', choices=['simulation', 'mission'], required=True)
    parser.add_argument('--mission', help="Check the mission directory names")
    parser.add_argument(
        '--simulation', choices=['TEST', 'legacy', 'FAIL', 'DEMO'])
    args = parser.parse_args()

    # mission_path = get_mission_path()
    try:
        if args.mode == 'mission':
            if not args.mission:
                raise ValueError("No mission has been provided")
            mission_path = os.path.join(get_mission_path(), args.mission)
            if not os.path.exists(mission_path):
                raise FileNotFoundError(
                    f"No mission direction found at: {mission_path}")
            if str(args.mission).lower() == "test":
                raise NotImplementedError("Test has not been implemented")
            slogger.info(f"Starting mission replay for {args.mission}")

            processed_packets = process_csv_packets(
                MIN_TIMESTAMP_MS, mission_path)
        else:
            from backend.simulation.run_simulation import get_replay_sim_data
            if not args.simulation:
                raise ValueError(
                    "No simulation was selected, required for simulation mode")
            if args.simulation != "TEST" and args.simulation != "DEMO":
                raise NotImplementedError(
                    f"The simulation mode: {args.simulation} has not been implemented yet")

            processed_packets = get_replay_sim_data()
            slogger.info(f"Starting simulation replay for {args.simulation}")

        if processed_packets is None:
            raise ValueError(
                "No packets have been received, replay data is empty")

        MockPacket.initialize_settings(
            config.load_config()[
                'emulation'], FAKE_DEVICE_NAME=args.device_rocket
        )

        # Will need to valid timeout before the gaps between packets may be extremely large
        # When replaying the packets the delay will cause an error when trying to shut down
        valid_timeout = validate_timeout_skip(
            processed_packets, MIN_TIMESTAMP_MS)
        if (args.simulation == "DEMO"):
            while not service_helper.time_to_stop():
                slogger.warning(
                    "STARTING UP DEMO MODE, THIS WILL RUN UNTIL STOPPED")
                replay_packets(processed_packets, valid_timeout)
                slogger.info("FINISHED SENDING PACKETS FOR DEMO")
        else:
            slogger.warning("Running the replay a single time")
            replay_packets(processed_packets, valid_timeout)
            slogger.info("FINISHED SENDING PACKETS")
    except ValueError as ve:
        slogger.error(
            f"Value Error in replay system: {str(ve)}")
        raise

    except FileNotFoundError as fe:
        slogger.error(f"File not found: {str(fe)}")
        raise

    except NotImplementedError as nie:
        slogger.error(f"Feature has not been implemented: {str(nie)}")
        raise

    except Exception as e:
        slogger.error(f"Something has gone wrong: {str(e)}")
        raise


if __name__ == "__main__":
    main()
