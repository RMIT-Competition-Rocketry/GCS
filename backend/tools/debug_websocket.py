import asyncio
import websockets
import json


async def pretty_print_json(uri):
    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")
        while True:
            try:
                message = await websocket.recv()
                try:
                    json_data = json.loads(message)
                    # print(json.dumps(json_data, indent=4))
                    if json_data["id"] == 3:
                        print(json_data["data"]["flightState"])
                except json.JSONDecodeError:
                    print("Non-JSON message received:")
                    print(message)
            except websockets.ConnectionClosed:
                print("WebSocket connection closed.")
                break

if __name__ == "__main__":
    uri = "ws://localhost:1887"
    asyncio.run(pretty_print_json(uri))
