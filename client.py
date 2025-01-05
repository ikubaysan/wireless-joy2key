# client.py
import asyncio
import websockets
import logging

class WebSocketClient:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    async def listen(self):
        uri = f"ws://{self.ip}:{self.port}"
        async with websockets.connect(uri) as websocket:
            logging.info(f"Connected to server at {uri}")
            try:
                while True:
                    message = await websocket.recv()
                    logging.info(f"Received: {message}")
            except websockets.exceptions.ConnectionClosed:
                logging.info("Connection closed.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    client = WebSocketClient(ip="localhost", port=8765)
    try:
        asyncio.run(client.listen())
    except KeyboardInterrupt:
        logging.info("Client exited.")
