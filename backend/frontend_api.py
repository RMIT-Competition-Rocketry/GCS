import asyncio
import sys
import json
import websockets
import zmq
from google.protobuf.json_format import MessageToDict
import proto.generated.AV_TO_GCS_DATA_1_pb2 as AV_TO_GCS_DATA_1_pb
import proto.generated.AV_TO_GCS_DATA_2_pb2 as AV_TO_GCS_DATA_2_pb
import proto.generated.AV_TO_GCS_DATA_3_pb2 as AV_TO_GCS_DATA_3_pb
import proto.generated.GSE_TO_GCS_DATA_1_pb2 as GSE_TO_GCS_DATA_1_pb
import proto.generated.GSE_TO_GCS_DATA_2_pb2 as GSE_TO_GCS_DATA_2_pb
import backend.process_logging as slogger  # slog 4 lyf


async def zmq_to_websocket(websocket, ZMQ_SUB_SOCKET):
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    try:
        sub_socket.connect(ZMQ_SUB_SOCKET)
    except zmq.ZMQError as e:
        slogger.error(f"Connection error: {e}")
        return
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

    # Create a mapping of packet IDs to their proto definitions
    packet_handlers = {
        3: AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1,
        4: AV_TO_GCS_DATA_2_pb.AV_TO_GCS_DATA_2,
        5: AV_TO_GCS_DATA_3_pb.AV_TO_GCS_DATA_3,
        6: GSE_TO_GCS_DATA_1_pb.GSE_TO_GCS_DATA_1,
        7: GSE_TO_GCS_DATA_2_pb.GSE_TO_GCS_DATA_2,
    }

    try:
        while True:
            # # Blocking
            message = sub_socket.recv()
            if len(message) > 1:
                # We've missed the ID publish message. Wait for next one
                continue

            packet_id = int.from_bytes(message, byteorder='big')
            message = sub_socket.recv()

            if len(message) == 1:
                # Something failed and we've got a new ID instead of the last message.
                new_erronous_packet_id = int.from_bytes(
                    message, byteorder='big')
                slogger.error(
                    f"Event viewer subscription did not find last message with ID: {packet_id}. Instead got new ID: {new_erronous_packet_id}")
                continue

            if packet_id in packet_handlers:
                proto_object = packet_handlers[packet_id]()
                proto_object.ParseFromString(message)
                # Use the parsed proto_object, not the raw message
                proto_dict_data = MessageToDict(proto_object)
            else:
                slogger.error(f"Unexpected packet ID: {packet_id}")
                proto_dict_data = {}

            message_json = json.dumps(proto_dict_data)

            # Send JSON message to WebSocket
            await websocket.send(message_json)
    except websockets.ConnectionClosed:
        print("WebSocket connection closed")
    finally:
        sub_socket.close()
        context.term()


# Modified to create a handler that includes the ZMQ socket
async def handler(websocket):
    await zmq_to_websocket(websocket, IPC_ADDRESS)


async def amain():
    server = await websockets.serve(handler, WEBSOCKET_HOST, WEBSOCKET_PORT)

    slogger.info(
        f"WebSocket server started at ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")

    # Keep the server running indefinitely
    await asyncio.Future()


def main():
    SOCKET_PATH = sys.argv[sys.argv.index('--socket-path') + 1]
    global WEBSOCKET_HOST, WEBSOCKET_PORT
    WEBSOCKET_HOST = "localhost"
    WEBSOCKET_PORT = 1887  # First year of RMIT

    global IPC_ADDRESS
    IPC_ADDRESS = f"ipc:///tmp/{SOCKET_PATH}_pub.sock"

    # Run the async main using asyncio.run() which properly handles the event loop
    asyncio.run(amain())


if __name__ == "__main__":
    main()
