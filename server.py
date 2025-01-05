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

        directions = ["up", "down", "left", "right"]
        logger.info("Please press a button or move a control for each direction.")
        for direction in directions:
            while True:
                event = pygame.event.wait()
                if event.type == pygame.JOYBUTTONDOWN:
                    self.input_mapping[direction] = ("button", event.button)
                    logger.info(f"Mapped {direction} to button {event.button}.")
                    break
                # elif event.type == pygame.JOYAXISMOTION and abs(event.value) > 0.5:
                #     self.input_mapping[direction] = ("axis", event.axis, event.value)
                #     logger.info(f"Mapped {direction} to axis {event.axis} with value {event.value:.2f}.")
                #     break
                # elif event.type == pygame.JOYHATMOTION:
                #     self.input_mapping[direction] = ("hat", event.hat, event.value)
                #     logger.info(f"Mapped {direction} to hat {event.hat} with value {event.value}.")
                #     break

    def read_inputs(self) -> Optional[str]:
        if not self.selected_controller:
            raise RuntimeError("No controller selected.")

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.JOYBUTTONDOWN:
                for direction, mapping in self.input_mapping.items():
                    if mapping[0] == "button" and mapping[1] == event.button:
                        return direction
            # elif event.type == pygame.JOYAXISMOTION:
            #     for direction, mapping in self.input_mapping.items():
            #         if (
            #             mapping[0] == "axis"
            #             and mapping[1] == event.axis
            #             and (mapping[2] > 0 and event.value > 0.5)
            #             or (mapping[2] < 0 and event.value < -0.5)
            #         ):
            #             return direction
            # elif event.type == pygame.JOYHATMOTION:
            #     for direction, mapping in self.input_mapping.items():
            #         if mapping[0] == "hat" and mapping[1] == event.hat and mapping[2] == event.value:
            #             return direction

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
                input_direction = self.manager.read_inputs()
                if input_direction:
                    logger.info(f"Sending input: {input_direction}")
                    await websocket.send(input_direction)
                await asyncio.sleep(0.01)
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
