import datetime
import zmq
import os
import csv
import sys
import proto.generated.AV_TO_GCS_DATA_1_pb2 as AV_TO_GCS_DATA_1_pb
from pprint import pprint
from typing import List

# Just prints useful information from AV and saves it to file


class Packet:
    _setup: bool = False
    # There are many other class variables defined in the setup method

    @classmethod
    def _setup_logging(cls):
        # Create the logging file and write headers
        # First, make a directory for each of the CSV files per session
        session_log_folder = os.path.join(
            "logs", cls._VIEWER_STARTUP_TIMESTAMP_STR)

        # This should only ever loop more than once if you're running this
        # method in many instances over the same second. So never really
        dir_num = 1
        while (os.path.isdir(session_log_folder) is True):
            session_log_folder += f"_{dir_num}"
            if dir_num > 10:
                raise Exception("Error: Creating too many logging directories")

        try:
            os.mkdir(session_log_folder)
        except Exception as e:
            print(
                f"Error: Failed to create logging directory: {e} for {session_log_folder}")
            raise

        cls._session_log_folder = session_log_folder

        # Base these off the proto files
        # Name each subclass after these
        # TODO: After the proto files are finalised, update these
        cls._CSV_FILES_WITH_HEADERS = {
            "GCS_TO_AV_STATE_CMD": ["", "", "", "", ""],
            "GCS_TO_GSE_STATE_CMD": ["", "", "", "", ""],
            "AV_TO_GCS_DATA_1": ["FlightState",
                                 "dual_board_connectivity_state_flag",
                                 "recovery_checks_complete_and_flight_ready",
                                 "GPS_fix_flag",
                                 "payload_connection_flag",
                                 "camera_controller_connection_flag",
                                 "accel_low_x",
                                 "accel_low_y",
                                 "accel_low_z",
                                 "accel_high_x",
                                 "accel_high_y",
                                 "accel_high_z",
                                 "gyro_x",
                                 "gyro_y",
                                 "gyro_z",
                                 "altitude",
                                 "velocity",
                                 "apogee_primary_test_complete",
                                 "apogee_secondary_test_complete",
                                 "apogee_primary_test_results",
                                 "apogee_secondary_test_results",
                                 "main_primary_test_complete",
                                 "main_secondary_test_complete",
                                 "main_primary_test_results",
                                 "main_secondary_test_results",
                                 "broadcast_flag"
                                 ],
            "AV_TO_GCS_DATA_2": ["", "", "", "", ""],
            "AV_TO_GCS_DATA_3": ["", "", "", "", ""],
            "GSE_TO_GCS_DATA_1": ["", "", "", "", ""],
            "GSE_TO_GCS_DATA_2": ["", "", "", "", ""],
            "GSE_TO_GCS_DATA_3": ["", "", "", "", ""],
        }

        # As the directory is named per instance, this should not need to be
        # looped for name uniqueness
        for file_name, headers in cls._CSV_FILES_WITH_HEADERS.items():
            csv_path = os.path.join(
                cls._session_log_folder, f"{file_name}.csv")
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp_ms"] + headers)

    @classmethod
    def setup(cls,
              STARTUP_TIME: datetime.datetime,
              CREATE_LOGS: bool):

        cls._VIEWER_STARTUP_TIMESTAMP = STARTUP_TIME
        cls._VIEWER_STARTUP_TIMESTAMP_STR = \
            STARTUP_TIME.strftime("%Y-%m-%d_%H-%M-%S")

        if (CREATE_LOGS):
            cls._setup_logging()

        cls._LOGGING_ENABLED = CREATE_LOGS

        cls._setup = True

    def __init__(self, packet_id, serial_data):
        self._PACKET_ID = packet_id
        self._SERIAL_DATA = serial_data
        self._packet_name = self.__class__.__name__  # Automatically set for subclasses

        if not self.__class__._setup == True:
            raise Exception("Error: Logging not set up")

    def _log_to_csv(self, data: List[str]):
        """Log data to the respective CSV file

        Args:
            data (List[str]): A list of values to place in the row of the CSV file

        Raises:
            Exception: Incorrect file name
        """

        if not self.__class__._LOGGING_ENABLED:
            print("Error: Logging to csv disabled but attempted anyway")
            return

        if self._packet_name not in self.__class__._CSV_FILES_WITH_HEADERS.keys():
            raise Exception(
                f"Error: Unknown packet name: {self._packet_name}. Please ensure sub-class is named verbatim to cls._CSV_FILES_WITH_HEADERS")

        file_name = self._packet_name + ".csv"

        with open(os.path.join(self.__class__._session_log_folder, file_name), "a") as f:
            writer = csv.writer(f)
            timestamp = datetime.datetime.now() - self.__class__._VIEWER_STARTUP_TIMESTAMP
            writer.writerow([timestamp.total_seconds()*1000] + data)


class AV_TO_GCS_DATA_1(Packet):
    def __init__(self):
        super().__init__(3, None)


def main(SOCKET_PATH, CREATE_LOGS):
    VIEWER_STARTUP_TIMESTAMP = datetime.datetime.now()
    Packet.setup(VIEWER_STARTUP_TIMESTAMP, CREATE_LOGS)
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)

    # Construct the full IPC path
    ipc_address = f"ipc:///tmp/{SOCKET_PATH}_pub.sock"
    print(f"Info: Connecting to {ipc_address}...")

    try:
        sub_socket.connect(ipc_address)
    except zmq.ZMQError as e:
        print(f"Erorr: Connection error: {e}")
        return

    sub_socket.setsockopt_string(zmq.SUBSCRIBE, '')

    print("Info: Listening for messages...")

    # Setup handler objects
    AV_TO_GCS_DATA_1_handler = AV_TO_GCS_DATA_1()

    while True:
        try:
            message = sub_socket.recv(flags=zmq.NOBLOCK)
            if len(message) > 1:
                # We've missed the ID publish message. Wait for next one
                continue
            packet_id = int.from_bytes(message, byteorder='big')
            print("Debug: Packet ID: ", packet_id)
            message = sub_socket.recv()

            match packet_id:
                case 3:
                    # AV packet
                    AV_TO_GCS_DATA_1_packet = AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1()
                    AV_TO_GCS_DATA_1_packet.ParseFromString(message)
                    if CREATE_LOGS:
                        AV_TO_GCS_DATA_1_handler._log_to_csv(
                            # This obviously assumes that the order of the fields in
                            # the proto file is the same as the order as the CSV headers
                            # TODO Make this expclit when you have all the time in the world
                            [x[1] for x in AV_TO_GCS_DATA_1_packet.ListFields()]
                        )
                    pprint(AV_TO_GCS_DATA_1_packet)
                    sys.stdout.flush()  # Ensures output is immediately written
                case _:
                    print(f"Erorr: Unexpected packet ID: {packet_id}")
        except zmq.Again:
            # No message received, sleep to prevent CPU spin
            pass
        except KeyboardInterrupt:
            # As soon as the CLI gets the interrupt, a race condition starts and child cleanup is not guaranteed
            print("Warning: Keyboard interrupt received. Listening stopping")


if __name__ == "__main__":
    try:
        SOCKET_PATH = sys.argv[sys.argv.index('--socket-path') + 1]
    except ValueError:
        print("Error: Failed to find socket path in arguments for event viewer")
        raise
    try:
        create_logs = '--no-log' in sys.argv
    except ValueError:
        print("Error: Failed to find socket path in arguments for event viewer")
        create_logs = True

    main(SOCKET_PATH, create_logs)
    print("Info: Event viewer stopped")
