import zmq
import sys
import proto.generated.AV_TO_GCS_DATA_1_pb2 as AV_TO_GCS_DATA_1
from pprint import pprint

# Just prints useful information from AV and saves it to file


def main(socket_path):
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)

    # Construct the full IPC path
    ipc_address = f"ipc:///tmp/{socket_path}_pub.sock"
    print(f"Info: Connecting to {ipc_address}...")

    try:
        sub_socket.connect(ipc_address)
    except zmq.ZMQError as e:
        print(f"Erorr: Connection error: {e}")
        return

    sub_socket.setsockopt_string(zmq.SUBSCRIBE, '')

    print("Info: Listening for messages...")
    while True:
        try:
            message = sub_socket.recv(flags=zmq.NOBLOCK)
            if len(message) > 1:
                # We've missed the ID publish message. Wait for next one
                continue
            packet_id = int.from_bytes(message, byteorder='big')
            print("Debug: Packet ID: ", packet_id)
            match packet_id:
                case 3:
                    # AV packet
                    message = sub_socket.recv()
                    AV_TO_GCS_DATA_1_packet = AV_TO_GCS_DATA_1.AV_TO_GCS_DATA_1()
                    AV_TO_GCS_DATA_1_packet.ParseFromString(message)
                    pprint(AV_TO_GCS_DATA_1_packet)
                    sys.stdout.flush()  # Ensures output is immediately written
                case _:
                    print(f"Erorr: Unexpected packet ID: {packet_id}")
        except zmq.Again:
            # No message received, sleep to prevent CPU spin
            pass


if __name__ == "__main__":
    print("Debug: Alive")
    try:
        SOCKET_PATH = sys.argv[sys.argv.index('--socket-path') + 1]
    except ValueError:
        print("Error: Failed to find socket path in arguments for event viewer")
        raise
    main(SOCKET_PATH)
