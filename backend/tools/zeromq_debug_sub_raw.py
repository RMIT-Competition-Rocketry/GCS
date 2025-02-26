import zmq
import argparse
from datetime import datetime
import signal
import hashlib
import backend.ansci as ansci

# Subscribes to the ZeroMQ PUB socket and prints received messages in hex and ASCII format


def format_hex(data):
    """Convert bytes to readable hex format"""
    return ' '.join(f"{byte:02x}" for byte in data)


def get_sha(data, length=8):
    """Compute the SHA-1 hash of data and return the first `length` characters of its hex digest.

    Args:
        data (bytes): The data to hash.
        length (int): Number of characters to return from the digest (default 8).

    Returns:
        str: The first `length` characters of the SHA-1 hash in hexadecimal.
    """
    sha_full = hashlib.sha1(data, usedforsecurity=False).hexdigest()
    return sha_full[:length]


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

    last_item = "UNINITIALISED"

    while True:
        try:
            message = sub_socket.recv(flags=zmq.NOBLOCK)
            if len(message) == 0:
                if last_item != "DATA" and last_item != "UNINITIALISED":
                    match last_item:
                        case "ID":
                            print(ansci.FG_RED +
                                  f"MISSING:DATA ^^" + ansci.RESET)
                        case "DATA":
                            print(ansci.FG_RED +
                                  f"MISSING:ID ^^" + ansci.RESET)
                        case "NOTHING":
                            print(ansci.FG_RED +
                                  f"MISSING:?? ^^" + ansci.RESET)
                last_item = "NOTHING"
                color = ansci.BG_RED
            elif len(message) == 1:
                if last_item != "DATA" and last_item != "UNINITIALISED":
                    print(ansci.FG_RED + "LOST DATA ^^" + ansci.RESET)
                last_item = "ID"
                color = ansci.BG_BLUE
            else:
                if last_item != "ID" and last_item != "UNINITIALISED":
                    print(ansci.FG_RED + "LOST ID ^^" + ansci.RESET)
                last_item = "DATA"
                color = ansci.BG_GREEN

            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            hex_data = format_hex(message)
            sha_data = get_sha(message)
            print(
                f"[{timestamp}] {color}Received {len(message)} bytes:{ansci.RESET}")
            print(f"({sha_data}) {hex_data}")
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
