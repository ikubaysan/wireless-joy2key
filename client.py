import asyncio
import websockets
import logging
from pynput.keyboard import Controller, Key

class WebSocketClient:
    def __init__(self, ip: str, port: int, key_mapping: dict):
        self.ip = ip
        self.port = port
        self.key_mapping = key_mapping  # Map bit indexes to keys
        self.keyboard = Controller()
        self.current_state = {bit: 0 for bit in key_mapping}  # Track key states

    async def listen(self):
        uri = f"ws://{self.ip}:{self.port}"
        async with websockets.connect(uri) as websocket:
            logging.info(f"Connected to server at {uri}")
            try:
                while True:
                    message = await websocket.recv()
                    logging.info(f"Received: {message}")
                    self._process_message(message)
            except websockets.exceptions.ConnectionClosed:
                logging.info("Connection closed.")

    def _process_message(self, message: str):
        for bit_index, key in self.key_mapping.items():
            is_pressed = int(message[bit_index])
            if is_pressed != self.current_state[bit_index]:
                if is_pressed:
                    self._press_key(key)
                else:
                    self._release_key(key)
                self.current_state[bit_index] = is_pressed

    def _press_key(self, key):
        logging.info(f"Pressing key: {key}")
        self.keyboard.press(key)

    def _release_key(self, key):
        logging.info(f"Releasing key: {key}")
        self.keyboard.release(key)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Define the mapping of bit indexes to keys
    key_mapping = {
        # 0: 'a',  # Bit index 0 -> 'a' key
        # 1: 'z',  # Bit index 1 -> 'z' key
        # 2: 'x',  # Bit index 2 -> 'x' key
        # 3: 'c',  # Bit index 3 -> 'c' key

        0: Key.left,
        1: Key.down,
        2: Key.up,
        3: Key.right,

    }

    client = WebSocketClient(ip="localhost", port=7482, key_mapping=key_mapping)
    try:
        asyncio.run(client.listen())
    except KeyboardInterrupt:
        logging.info("Client exited.")
