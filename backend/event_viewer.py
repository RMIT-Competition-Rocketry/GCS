import datetime
import zmq
import os
import csv
import sys
from google.protobuf.message import Message as PbMessage
import proto.generated.AV_TO_GCS_DATA_1_pb2 as AV_TO_GCS_DATA_1_pb
from typing import List, Dict
import backend.process_logging as slogger  # slog deez nuts
import backend.ansci as ansci

# Just prints useful information from AV and saves it to csv file


class Packet:
    # Updated in _setup_logging
    _setup: bool = False

    # Defined in _setup_logging
    _session_log_folder: str = None
    _CSV_FILES_WITH_HEADERS: Dict[str, str] = None

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
            slogger.error(
                f"Failed to create logging directory: {e} for {session_log_folder}")
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
            # slogger.error("Logging to csv disabled but attempted anyway")
            return

        if self._packet_name not in self.__class__._CSV_FILES_WITH_HEADERS.keys():
            raise Exception(
                f"Error: Unknown packet name: {self._packet_name}. Please ensure sub-class is named verbatim to cls._CSV_FILES_WITH_HEADERS")

        file_name = self._packet_name + ".csv"

        with open(os.path.join(self.__class__._session_log_folder, file_name), "a") as f:
            writer = csv.writer(f)
            timestamp = datetime.datetime.now() - self.__class__._VIEWER_STARTUP_TIMESTAMP
            writer.writerow([timestamp.total_seconds()*1000] + data)

    def process(self, PROTO_DATA: PbMessage) -> None:
        """How to handle each new packet from an event viewer perspective
        this includes logging to file and printing important information to console

        Args:
            PROTO_DATA (PbMessage): The protobuf object
        """
        # `PROTO_DATA.ListFields()[0][0].name` returns the field name
        # `PROTO_DATA.ListFields()[0][1]` returns the value
        # This will just assume it's all in order of the csv headers for now.
        # Git issue #26
        data_as_string = [x[1] for x in PROTO_DATA.ListFields()]
        # `Logging enabled` check is internal to the csv function
        self._log_to_csv(data_as_string)
        # Please call super on this and add printing events afterwards


class GCS_TO_AV_STATE_CMD(Packet):
    # Static flags to be accessed and updated by result packet AV_TO_GCS_DATA_1
    awaiting_results_apogee_primary = False
    awaiting_results_apogee_secondary = False
    awaiting_results_main_primary = False
    awaiting_results_main_secondary = False

    def __init__(self):
        super().__init__(0x01, None)


class AV_TO_GCS_DATA_1(Packet):
    def __init__(self):
        super().__init__(0x03, None)
        # How long to wait before printing basic information
        self._INFORMATION_TIMEOUT = datetime.timedelta(seconds=1)
        self._last_information_display_time = datetime.datetime.min
        self._last_flight_state: AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState = None
        self._last_state_flags = {"dual_board_connectivity_state_flag": None,
                                  "recovery_checks_complete_and_flight_ready": None,
                                  "GPS_fix_flag": None,
                                  "payload_connection_flag": None,
                                  "camera_controller_connection_flag": None}
        self._last_test_details = {"apogee_primary_test_complete": None,
                                   "apogee_secondary_test_complete": None,
                                   "apogee_primary_test_results": None,
                                   "apogee_secondary_test_results": None,
                                   "main_primary_test_complete": None,
                                   "main_secondary_test_complete": None,
                                   "main_primary_test_results": None,
                                   "main_secondary_test_results": None}
        self._supersonic = False

    def _process_flight_state(self, PROTO_DATA: AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1) -> None:
        if self._last_flight_state != PROTO_DATA.flightState:
            # Flight state has changed. Please update it and notify
            self._last_flight_state = PROTO_DATA.flightState
            flight_state_name = AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.Name(
                PROTO_DATA.flightState)
            match PROTO_DATA.flightState:
                case \
                        AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.PRE_FLIGHT_FLIGHT_READY | \
                        AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.LAUNCH | \
                        AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.COAST | \
                        AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.APOGEE | \
                        AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.DECENT | \
                        AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.LANDED:
                    slogger.info(
                        f"Flight state changed to {flight_state_name}")
                case AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.PRE_FLIGHT_NO_FLIGHT_READY:
                    slogger.warning(
                        f"Flight state changed to {flight_state_name}")
                case AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.OH_NO:
                    slogger.critical(
                        f"Flight state changed to {flight_state_name}")
                case _:
                    slogger.error(f"Unknown flight state {flight_state_name}")

            # Extra case for printing apogee estimation
            if PROTO_DATA.flightState == AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1.FlightState.APOGEE:
                __ft_estimation = AV_TO_GCS_DATA_1._mt_to_ft(
                    PROTO_DATA.altitude)
                slogger.success(
                    f"Instantaneous Apogee estimation: {__ft_estimation} ft")

    def _process_state_flags(self, PROTO_DATA: AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1) -> None:
        # Info level for 0 -> 1 and warning for 1 -> 0
        for state_flag_name, state_flag_value in PROTO_DATA.ListFields()[1:6]:
            state_flag_name = state_flag_name.name
            if self._last_state_flags[state_flag_name] != state_flag_value:
                # Something changed
                if state_flag_value == 1:
                    slogger.info(
                        f"{state_flag_name} changed to {state_flag_value}")
                else:
                    slogger.warning(
                        f"{state_flag_name} changed to {state_flag_value}")
            # Update historical value
            self._last_state_flags[state_flag_name] = state_flag_value

    def _process_AV_tests(self, PROTO_DATA: AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1) -> None:
        def __process_test(DATA_TEST_COMPLETE: bool,
                           KEY_TEST_COMPLETE: str,
                           DATA_TEST_RESULTS: bool,
                           KEY_TEST_RESULTS: str,
                           AWAITING_TEST_RESULTS: bool) -> bool:
            """Repeated logic for each code complete and result pair. Likely to change after White Cliffs

            ```
            Function waiting_for_test()
                RETURN true if last `GCS to AV State CMD` asked for a test, false otherwise

            Function process_test()
                // TC means test complete bit
                // TR means test result bit

                TC_changed <- false

                IF (TC has changed) THEN
                    TC_changed <- true
                    IF (waiting_for_test()) THEN
                        IF (TC == 1) THEN
                            PRINT "good: test complete"
                        ELSE IF (TC == 0) THEN
                            PRINT "bad: test failed to complete"
                        ENDIF

                        IF (TR == 1) THEN
                            PRINT "good: continuity passed"
                        ELSE IF (TR == 0) THEN
                            PRINT "bad: continuity failed"
                        ENDIF
                    ELSE THEN
                        IF (TC == 1) THEN
                            PRINT "bad: unprompted test completed"
                        ELSE IF (TC == 0) THEN
                            // Do nothing. This is okay.
                            // Probably just returning back to default state
                        ENDIF
                    ENDIF
                ENDIF

                IF ((TR has changed) AND (!TC_changed)) THEN
                    PRINT "bad: test result changed without test completion"
                ENDIF
            ```

            Args:
                DATA_TEST_COMPLETE (bool): PROTO_DATA.apogee_primary_test_complete
                KEY_TEST_COMPLETE (str): The name of the proto field to match the key in self._last_test_details # "apogee_primary_test_complete"
                DATA_TEST_RESULTS (bool): PROTO_DATA.apogee_primary_test_results
                KEY_TEST_RESULTS (str): The name of the proto field to match the key in self._last_test_details # "apogee_primary_test_results"
                AWAITING_TEST_RESULTS (bool): GCS_TO_AV_STATE_CMD.awaiting_results_main_primary

            Returns:
                bool: caller_awaiting_results. Please assign the static class GCS_TO_AV_STATE_CMD and it's respective awaiting_results_... field with this return value
            """

            # Check results against what we were waiting for
            # If changed:
            #   If waiting: info level if complete, error if not
            #   If not waiting: error level if complete, info if not (contradiction)
            data_test_complete_changed = False
            caller_awaiting_results = True
            # Run assumption that you've setup and named keys correctly with descriptors
            if (DATA_TEST_COMPLETE !=
                    self._last_test_details[KEY_TEST_COMPLETE]):
                # This value has changed ^
                data_test_complete_changed = True
                # Were we waiting for a rest result?
                if AWAITING_TEST_RESULTS:
                    # Yes we were. Hopefully it's complete and show the results
                    if DATA_TEST_COMPLETE:
                        slogger.success(f"{KEY_TEST_COMPLETE} complete")
                    else:
                        slogger.error(f"{KEY_TEST_COMPLETE} not complete")
                    # Now update the object. We aren't waiting anymore
                    caller_awaiting_results = False
                elif DATA_TEST_COMPLETE:
                    # We weren't waiting for this result.
                    # This is odd if it just ran, but not if it's changing back to 0
                    slogger.error(f"Unprompted {KEY_TEST_COMPLETE} complete")

                # Update history of changed complete condition
                self._last_test_details[KEY_TEST_COMPLETE] = DATA_TEST_COMPLETE
                # Print the results because test result has changed
                if DATA_TEST_RESULTS == 1:
                    # Continuity. hell yeah
                    slogger.success(f"{KEY_TEST_RESULTS}: Continuity")
                else:
                    slogger.error(f"{KEY_TEST_RESULTS}: No Continuity")

            # Have the results changed when the test complete flag has not?
            if ((DATA_TEST_RESULTS != self._last_test_details[KEY_TEST_RESULTS])
                    and not data_test_complete_changed):
                slogger.error(
                    f"{KEY_TEST_RESULTS} changed without test completion")

            # Update historical test values too
            self._last_test_details[KEY_TEST_RESULTS] = DATA_TEST_RESULTS

            return caller_awaiting_results

        GCS_TO_AV_STATE_CMD.awaiting_results_apogee_primary = __process_test(
            PROTO_DATA.apogee_primary_test_complete,
            "apogee_primary_test_complete",
            PROTO_DATA.apogee_primary_test_results,
            "apogee_primary_test_results",
            GCS_TO_AV_STATE_CMD.awaiting_results_apogee_primary
        )
        GCS_TO_AV_STATE_CMD.awaiting_results_apogee_secondary = __process_test(
            PROTO_DATA.apogee_secondary_test_complete,
            "apogee_secondary_test_complete",
            PROTO_DATA.apogee_secondary_test_results,
            "apogee_secondary_test_results",
            GCS_TO_AV_STATE_CMD.awaiting_results_apogee_secondary
        )
        GCS_TO_AV_STATE_CMD.awaiting_results_main_primary = __process_test(
            PROTO_DATA.main_primary_test_complete,
            "main_primary_test_complete",
            PROTO_DATA.main_primary_test_results,
            "main_primary_test_results",
            GCS_TO_AV_STATE_CMD.awaiting_results_main_primary
        )
        GCS_TO_AV_STATE_CMD.awaiting_results_main_secondary = __process_test(
            PROTO_DATA.main_secondary_test_complete,
            "main_secondary_test_complete",
            PROTO_DATA.main_secondary_test_results,
            "main_secondary_test_results",
            GCS_TO_AV_STATE_CMD.awaiting_results_main_secondary
        )

    @staticmethod
    def _mt_to_ft(meters):
        return meters * 3.28084

    def process(self, PROTO_DATA: AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1) -> None:
        super().process(PROTO_DATA)

        # Useful docs: https://googleapis.dev/python/protobuf/latest/google/protobuf/descriptor.html

        # State Flags
        # Check if the flight state has changed
        self._process_flight_state(PROTO_DATA)

        # Now list any other changes that could have happened.
        # Info level for 0 -> 1 and warning for 1 -> 0
        self._process_state_flags(PROTO_DATA)

        # Supersonic alert
        # (idk if we get this fast)
        # (refer to physics team in case we can calculate exact value)
        SUPERSONIC_VELOCITY = 343
        if PROTO_DATA.velocity >= SUPERSONIC_VELOCITY and self._supersonic == False:
            # Coolest line of code I've ever written btw
            slogger.info("Supersonic flight detected")
            self._supersonic = True
        elif self._supersonic and PROTO_DATA.velocity < SUPERSONIC_VELOCITY:
            slogger.info("Supersonic flight ended")
            self._supersonic = False

        # Regular infomation updates
        if datetime.datetime.now() - self._last_information_display_time > self._INFORMATION_TIMEOUT:
            # Print basic information
            ALT_M = PROTO_DATA.altitude
            ALT_FT = AV_TO_GCS_DATA_1._mt_to_ft(PROTO_DATA.altitude)
            VELOCITY = PROTO_DATA.velocity

            if ALT_FT <= 10000:
                alt_color = ansci.BG_GREEN + ansci.FG_BLACK  # Ideal altitude: green
            else:
                alt_color = ansci.BG_RED    # Over the target: red

            if VELOCITY <= 180:
                vel_color = ansci.BG_BLUE
            elif VELOCITY <= 200:
                vel_color = ansci.BG_CYAN
            elif VELOCITY <= 240:
                vel_color = ansci.BG_GREEN
            elif VELOCITY <= 270:
                vel_color = ansci.BG_YELLOW
            else:
                vel_color = ansci.BG_RED

            # < left aligned, 11 chars reserved, .2f float with 2 decimal places
            slogger.info(
                f"{alt_color}Altitude: {ALT_M:<8.3f}m {ALT_FT:<9.3f}ft{ansci.RESET}")
            slogger.info(
                f"{vel_color}Velocity: {VELOCITY:<8.3f}m/s{ansci.RESET}")
            self._last_information_display_time = datetime.datetime.now()

        self._process_AV_tests(PROTO_DATA)

        # Notify if moving to broadcast
        if PROTO_DATA.broadcast_flag:
            slogger.info(
                "@@@@@@@@@ FC MOVING TO BROADCAST MODE, GCS STOPPING TRANSMISSION @@@@@@@@@")


def main(SOCKET_PATH, CREATE_LOGS):
    VIEWER_STARTUP_TIMESTAMP = datetime.datetime.now()
    Packet.setup(VIEWER_STARTUP_TIMESTAMP, CREATE_LOGS)
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)

    # Construct the full IPC path
    ipc_address = f"ipc:///tmp/{SOCKET_PATH}_pub.sock"
    slogger.info("Connecting to {ipc_address}...")

    try:
        sub_socket.connect(ipc_address)
    except zmq.ZMQError as e:
        slogger.error(f"Connection error: {e}")
        return

    sub_socket.setsockopt_string(zmq.SUBSCRIBE, '')

    # Keep "Listening for messages..." here or change the event starter callback
    slogger.info("Listening for messages...")

    # Setup handler objects
    AV_TO_GCS_DATA_1_handler = AV_TO_GCS_DATA_1()
    GCS_TO_AV_STATE_CMD_handler = GCS_TO_AV_STATE_CMD()

    while True:
        try:
            message = sub_socket.recv(flags=zmq.NOBLOCK)
            if len(message) > 1:
                # We've missed the ID publish message. Wait for next one
                continue
            packet_id = int.from_bytes(message, byteorder='big')
            message = sub_socket.recv()

            match packet_id:
                case 3:
                    AV_TO_GCS_DATA_1_packet = AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1()
                    AV_TO_GCS_DATA_1_packet.ParseFromString(message)
                    AV_TO_GCS_DATA_1_handler.process(AV_TO_GCS_DATA_1_packet)
                case _:
                    slogger.error(f"Unexpected packet ID: {packet_id}")
        except zmq.Again:
            # No message received, sleep to prevent CPU spin
            pass
        except KeyboardInterrupt:
            # As soon as the CLI gets the interrupt, a race condition starts and child cleanup is not guaranteed
            slogger.warning("Keyboard interrupt received. Listening stopping")


if __name__ == "__main__":
    slogger.debug("Started event viewer")
    try:
        SOCKET_PATH = sys.argv[sys.argv.index('--socket-path') + 1]
    except ValueError:
        slogger.error(
            "Failed to find socket path in arguments for event viewer")
        raise
    try:
        create_logs = '--no-log' in sys.argv
    except ValueError:
        slogger.error(
            "Failed to find socket path in arguments for event viewer")
        create_logs = True

    main(SOCKET_PATH, create_logs)
    slogger.info("Event viewer stopped")
