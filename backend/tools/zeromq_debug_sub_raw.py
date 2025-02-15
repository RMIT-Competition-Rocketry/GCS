import zmq
import argparse
from datetime import datetime
import signal

# Subscribes to the ZeroMQ PUB socket and prints received messages in hex and ASCII format


def format_hex(data):
    """Convert bytes to readable hex format"""
    return ' '.join(f"{byte:02x}" for byte in data)


def format_ascii(data):
    """Convert bytes to readable ASCII format, using '.' for non-readable characters"""
    return ''.join(chr(byte) if 32 <= byte <= 126 else '.' for byte in data)


def signal_handler(sig, frame):
    print("\nExiting...")
    exit(0)


def main(socket_path):
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)

    # Construct the full IPC path
    ipc_address = f"ipc:///tmp/{socket_path}_pub.sock"
    print(f"Connecting to {ipc_address}...")

    try:
        sub_socket.connect(ipc_address)
    except zmq.ZMQError as e:
        print(f"Connection error: {e}")
        return

    sub_socket.setsockopt_string(zmq.SUBSCRIBE, '')

    signal.signal(signal.SIGINT, signal_handler)

    print("Listening for messages...")
    while True:
        try:
            message = sub_socket.recv(flags=zmq.NOBLOCK)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            hex_data = format_hex(message)
            ascii_data = format_ascii(message)
            print(f"[{timestamp}] Received {len(message)} bytes:")
            print(f"({ascii_data}) {hex_data}")
        except zmq.Again:
            # No message received, sleep to prevent CPU spin
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ZeroMQ SUB client for LoRa interface")
    parser.add_argument("socket_path",
                        help="Base socket path name used in the C++ program (without _pub.sock)",
                        default="gcs_rocket")
    args = parser.parse_args()

    main(args.socket_path)
