import asyncio
import websockets
import pygame
import logging
from typing import List, Optional
import sys

def configure_console_logger(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

configure_console_logger()
logger = logging.getLogger(__name__)

class GameController:
    def __init__(self, index: int, name: str):
        self.index: int = index
        self.name: str = name

    def __str__(self) -> str:
        return f"{self.index}: {self.name}"

class GameControllerManager:
    def __init__(self) -> None:
        pygame.init()
        pygame.joystick.init()
        self.controllers: List[GameController] = []
        self.selected_controller: Optional[pygame.joystick.Joystick] = None
        self.input_mapping: dict = {}
        self.button_states = {"left": 0, "down": 0, "up": 0, "right": 0}
        self._load_controllers()

    def _load_controllers(self) -> None:
        self.controllers.clear()
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            self.controllers.append(GameController(index=i, name=joystick.get_name()))

    def list_controllers(self) -> List[GameController]:
        return self.controllers

    def select_controller(self, index: int) -> None:
        if index < 0 or index >= len(self.controllers):
            raise ValueError("Invalid controller index.")

        joystick = pygame.joystick.Joystick(index)
        joystick.init()
        self.selected_controller = joystick
        logger.info(f"Selected controller: {joystick.get_name()}")

    def configure_inputs(self) -> None:
        if not self.selected_controller:
            raise RuntimeError("No controller selected.")

        directions = ["left", "down", "up", "right"]
        logger.info("Please press a button for each direction.")
        for direction in directions:
            logger.info(f"Press the button for '{direction}':")
            while True:
                event = pygame.event.wait()
                if event.type == pygame.JOYBUTTONDOWN:
                    self.input_mapping[direction] = ("button", event.button)
                    logger.info(f"Mapped '{direction}' to button {event.button}.")
                    break

    def read_inputs(self) -> Optional[str]:
        if not self.selected_controller:
            raise RuntimeError("No controller selected.")

        events = pygame.event.get()
        state_changed = False

        for event in events:
            if event.type in [pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP]:
                is_pressed = 1 if event.type == pygame.JOYBUTTONDOWN else 0
                for direction, mapping in self.input_mapping.items():
                    if mapping[0] == "button" and mapping[1] == event.button:
                        if self.button_states[direction] != is_pressed:
                            self.button_states[direction] = is_pressed
                            state_changed = True

        if state_changed:
            # Construct state string in order: bit 0 - left, bit 1 - down, bit 2 - up, bit 3 - right
            bits = [
                str(self.button_states["left"]),
                str(self.button_states["down"]),
                str(self.button_states["up"]),
                str(self.button_states["right"]),
            ]
            state_string = "".join(bits)
            return state_string

        return None


class WebSocketServer:
    def __init__(self, ip: str, port: int, manager: GameControllerManager):
        self.ip = ip
        self.port = port
        self.manager = manager

    async def _handler(self, websocket, path):
        logger.info(f"Client connected: {path}")
        try:
            while True:
                state_string = self.manager.read_inputs()
                if state_string:
                    logger.info(f"Sending state: {state_string}")
                    await websocket.send(state_string)
                await asyncio.sleep(0.001)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected.")

    async def run(self):
        async with websockets.serve(self._handler, self.ip, self.port):
            logger.info(f"WebSocket server started at {self.ip}:{self.port}")
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    manager = GameControllerManager()
    controllers = manager.list_controllers()

    if not controllers:
        logger.info("No controllers found.")
        exit(0)

    logger.info("Available Controllers:")
    for controller in controllers:
        logger.info(controller)

    try:
        selected_index = int(input("Select a controller by index: "))
        manager.select_controller(selected_index)
        manager.configure_inputs()

        server = WebSocketServer(ip="localhost", port=8765, manager=manager)
        asyncio.run(server.run())
    except ValueError:
        logging.error("Invalid input. Please enter a valid index.")
    except RuntimeError as e:
        logging.error(e)
