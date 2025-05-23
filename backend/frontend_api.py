from backend.includes_python.mach import Mach
import backend.includes_python.process_logging as slogger
import backend.proto.generated.GSE_TO_GCS_DATA_2_pb2 as GSE_TO_GCS_DATA_2_pb
import backend.proto.generated.GSE_TO_GCS_DATA_1_pb2 as GSE_TO_GCS_DATA_1_pb
import backend.proto.generated.AV_TO_GCS_DATA_3_pb2 as AV_TO_GCS_DATA_3_pb
import backend.proto.generated.AV_TO_GCS_DATA_2_pb2 as AV_TO_GCS_DATA_2_pb
import backend.proto.generated.AV_TO_GCS_DATA_1_pb2 as AV_TO_GCS_DATA_1_pb
import config.config as config
from google.protobuf.json_format import MessageToDict
import signal
import asyncio
import sys
import backend.tools.device_emulator as device_emulator
import json
import websockets
import zmq
import zmq.asyncio
import os

# Global flag for shutdown control
shutdown_event = asyncio.Event()

# NOTE. if this starts getting big, consider just adding things from this into
# the backend server output trhough protobuf anyway


def append_data(data: dict, PACKET_ID: int) -> dict:
    """Add data to the websocket structure that frontend uses

    Args:
        data (dict): protobuf data as a dict
        PACKET_ID (int): packet ID from the protobuf message

    Returns:
        dict: updated output
    """
    match PACKET_ID:
        case 3:
            data["mach_number"] = Mach.mach_from_alt_estimate(
                VELOCITY_M=data["velocity"],
                ALTITUDE_M=data["altitude"])
    return data


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
            try:
                events = await sub_socket.poll(timeout=100)
                if events:
                    packet_id = int.from_bytes(await sub_socket.recv(), 'big')
                    message = await sub_socket.recv()

                    if len(message) == 1:
                        new_id = int.from_bytes(message, 'big')
                        slogger.error(
                            f"Message mismatch: {packet_id} vs {new_id}")
                        continue

                    if packet_id in packet_handlers:
                        proto_object = packet_handlers[packet_id]()
                        proto_object.ParseFromString(message)
                        data = MessageToDict(proto_object)
                        data = append_data(data, packet_id)
                        output = {
                            "id": packet_id,
                            "data": data
                        }
                        try:
                            await websocket.send(json.dumps(output))
                        except websockets.ConnectionClosedOK:
                            pass
                    else:
                        slogger.error(f"Unexpected packet ID: {packet_id}")
                # Give event handler time to check shutdown event
                await asyncio.sleep(0.01)
            except websockets.ConnectionClosed:
                if not shutdown_event.is_set():
                    slogger.info(
                        "WebSocket connection closed from manager trigger")
                else:
                    slogger.info(
                        "WebSocket connection closed from ws client")
                break
            except Exception as e:
                slogger.error(f"Error fowarding data to websocket: {e}")
                if shutdown_event.is_set():
                    break
    finally:
        # Wait LINGER_TIME_MS before giving up on push request
        LINGER_TIME_MS = 300
        sub_socket.close(linger=LINGER_TIME_MS)
        context.term()


async def consumer(websocket):
    context = zmq.asyncio.Context()
    try:
        push_socket = context.socket(zmq.PUSH)
        SOCKET_PATH = os.path.abspath(os.path.join(
            os.path.sep, 'tmp', 'gcs_rocket_web_pull.sock')
        )
        LINGER_TIME_MS = 300
        push_socket.setsockopt(zmq.LINGER, LINGER_TIME_MS)
        push_socket.setsockopt(zmq.SNDHWM, 1)  # Limit send buffer to 1 message
        push_socket.connect(f"ipc://{SOCKET_PATH}")
        EXPECTED_ID = 0x09  # What ID should we relay to the server?
        try:
            async for message in websocket:
                if shutdown_event.is_set():
                    break
                try:
                    # TODO remove this after bundy testing
                    slogger.debug(f"Received ws message: {message}")
                    try:
                        message_json = json.loads(message)
                    except json.JSONDecodeError as e:
                        slogger.error(f"Invalid JSON received: {e}")
                        continue
                    if message_json.get("id") != EXPECTED_ID:
                        slogger.error(
                            f"Invalid packet ID for TX: {message_json.get('id')}. Expected {EXPECTED_ID}")
                        continue
                    data = message_json.get("data", None)
                    if data is None or len(data.keys()) == 0:
                        slogger.error("No data found in message")
                        continue
                    packet = build_packet(data)
                    packet_bytes = packet.get_payload_bytes(EXTERNAL=True)
                    # Prepend the manual control bool as a byte to tell server
                    manual_control = data.get("manualControl", False)
                    if isinstance(manual_control, bool):
                        prefix = bytes([0xFF if manual_control else 0x00])
                    else:
                        slogger.error(
                            f"Manual control field contains non-bool {manual_control}")
                        continue
                    packet_bytes = bytes(prefix) + packet_bytes
                    await push_socket.send(packet_bytes, flags=zmq.NOBLOCK)
                except json.JSONDecodeError as e:
                    slogger.error(f"Invalid JSON received: {e}")
                except KeyError as e:
                    slogger.error(f"Missing required key in message: {e}")
                except Exception as e:
                    slogger.error(
                        f"Error processing message: {e}. Socket may be full at HWM")
        except websockets.ConnectionClosedOK:
            if not shutdown_event.is_set():
                slogger.info(
                    "WebSocket connection closed in consumer from web side")
            else:
                slogger.info(
                    "WebSocket connection closed in consumer from manager trigger")
        except Exception as e:
            slogger.error(f"Consumer error: {e}")
    finally:
        slogger.debug("ZMQ socket closing")
        push_socket.close(linger=LINGER_TIME_MS)
        context.term()
        slogger.debug("Consumer ZMQ context terminated")


def build_packet(WEBSOCKET_DATA: dict) -> device_emulator.GCStoGSEManualControl:
    """An adaptor to convert internal websocket payload for manual actuation into lora packet GCS to GSE MANUAL CONTROL

    Args:
        WEBSOCKET_DATA (dict): Data in the format of post translation packet 0x09

    Returns:
        device_emulator.GCStoGSEManualControl: Output packet to be written to lora
    """

    PURGE_HIGH: bool = WEBSOCKET_DATA.get("solendoid1High", False)
    N2O_HIGH: bool = WEBSOCKET_DATA.get("solendoid2High", False)
    O2_HIGH: bool = WEBSOCKET_DATA.get("solendoid3High", False)
    states = {
        "MANUAL_PURGE": PURGE_HIGH,
        "O2_FILL_ACTIVATE": O2_HIGH,
        "SELECTOR_SWITCH_NEUTRAL_POSITION": False,
        "N2O_FILL_ACTIVATE": N2O_HIGH,
        "IGNITION_FIRE": False,
        "IGNITION_SELECTED": True,
        "GAS_FILL_SELECTED": True,
        "SYSTEM_ACTIVATE": True,
    }
    return device_emulator.GCStoGSEManualControl(**states)


async def handler(websocket):
    # start both producer and consumer
    producer_task = asyncio.create_task(
        zmq_to_websocket(websocket, IPC_ADDRESS))
    consumer_task = asyncio.create_task(consumer(websocket))

    try:
        # wait until one side throws an exception or shutdown is requested
        done, pending = await asyncio.wait(
            [producer_task, consumer_task],
            return_when=asyncio.FIRST_EXCEPTION
        )

        if shutdown_event.is_set():
            await websocket.close(code=1001, reason="Server shutting down")
    except Exception as e:
        slogger.error(f"Handler error: {e}")
    finally:
        for task in pending:
            task.cancel()
        await websocket.close()


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
        for ws in server.connections:
            await ws.close(code=1001, reason="Server shutdown")
        server.close()
        await server.wait_closed()
        slogger.info("Server shutdown complete")


def main():
    global WEBSOCKET_HOST, WEBSOCKET_PORT, IPC_ADDRESS

    WEBSOCKET_HOST = "0.0.0.0"
    WEBSOCKET_PORT = 1887

    if '--socket-path' in sys.argv:
        SOCKET_PATH = sys.argv[sys.argv.index('--socket-path') + 1]
        IPC_ADDRESS = f"ipc:///tmp/{SOCKET_PATH}_pub.sock"
    else:
        slogger.error("Missing required --socket-path argument")
        sys.exit(1)

    device_emulator.MockPacket.initialize_settings(
        config.load_config()['emulation'])

    try:
        asyncio.run(amain())
    finally:
        slogger.info("Application exited")


if __name__ == "__main__":
    main()
