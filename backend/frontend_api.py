import signal
import asyncio
import sys
import json
import websockets
import zmq
import zmq.asyncio
from google.protobuf.json_format import MessageToDict
import backend.proto.generated.AV_TO_GCS_DATA_1_pb2 as AV_TO_GCS_DATA_1_pb
import backend.proto.generated.AV_TO_GCS_DATA_2_pb2 as AV_TO_GCS_DATA_2_pb
import backend.proto.generated.AV_TO_GCS_DATA_3_pb2 as AV_TO_GCS_DATA_3_pb
import backend.proto.generated.GSE_TO_GCS_DATA_1_pb2 as GSE_TO_GCS_DATA_1_pb
import backend.proto.generated.GSE_TO_GCS_DATA_2_pb2 as GSE_TO_GCS_DATA_2_pb
import backend.process_logging as slogger

# Global flag for shutdown control
shutdown_event = asyncio.Event()


async def zmq_to_websocket(websocket, ZMQ_SUB_SOCKET):
    context = zmq.asyncio.Context()
    sub_socket = context.socket(zmq.SUB)
    try:
        sub_socket.connect(ZMQ_SUB_SOCKET)
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        packet_handlers = {
            3: AV_TO_GCS_DATA_1_pb.AV_TO_GCS_DATA_1,
            4: AV_TO_GCS_DATA_2_pb.AV_TO_GCS_DATA_2,
            5: AV_TO_GCS_DATA_3_pb.AV_TO_GCS_DATA_3,
            6: GSE_TO_GCS_DATA_1_pb.GSE_TO_GCS_DATA_1,
            7: GSE_TO_GCS_DATA_2_pb.GSE_TO_GCS_DATA_2,
        }

        while not shutdown_event.is_set():
            events = await sub_socket.poll(timeout=100)
            if events:
                packet_id = int.from_bytes(await sub_socket.recv(), 'big')
                message = await sub_socket.recv()

                if len(message) == 1:
                    new_id = int.from_bytes(message, 'big')
                    slogger.error(f"Message mismatch: {packet_id} vs {new_id}")
                    continue

                if packet_id in packet_handlers:
                    proto_object = packet_handlers[packet_id]()
                    proto_object.ParseFromString(message)
                    output = MessageToDict(proto_object)
                    output = {
                        "id": packet_id,
                        "data": output
                    }
                    await websocket.send(json.dumps(output))
                else:
                    slogger.error(f"Unexpected packet ID: {packet_id}")
            # Give event handler time to check shutdown event
            await asyncio.sleep(0.01)

    except websockets.ConnectionClosed:
        slogger.info("WebSocket connection closed")
    except Exception as e:
        slogger.error(f"ZMQ error: {e}")
    finally:
        # Wait LINGER_TIME_MS before giving up on push request
        LINGER_TIME_MS = 300
        sub_socket.close(linger=LINGER_TIME_MS)
        context.term()


async def handler(websocket):
    await zmq_to_websocket(websocket, IPC_ADDRESS)


async def amain():
    # Set up signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: shutdown_event.set())

    server = await websockets.serve(handler, WEBSOCKET_HOST, WEBSOCKET_PORT)
    slogger.info(
        f"WebSocket server started at ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")

    try:
        await shutdown_event.wait()
    finally:
        slogger.info("Shutting down server...")
        server.close()
        await server.wait_closed()
        slogger.info("Server shutdown complete")


def main():
    global WEBSOCKET_HOST, WEBSOCKET_PORT, IPC_ADDRESS

    WEBSOCKET_HOST = "localhost"
    WEBSOCKET_PORT = 1887

    if '--socket-path' in sys.argv:
        SOCKET_PATH = sys.argv[sys.argv.index('--socket-path') + 1]
        IPC_ADDRESS = f"ipc:///tmp/{SOCKET_PATH}_pub.sock"
    else:
        slogger.error("Missing required --socket-path argument")
        sys.exit(1)

    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        slogger.info("Keyboard interrupt received")
    finally:
        slogger.info("Application exited")


if __name__ == "__main__":
    main()
