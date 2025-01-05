# server.py
import asyncio
import websockets
import pygame
import logging
from typing import List, Optional

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
        logging.info(f"Selected controller: {joystick.get_name()}")

    def read_inputs(self) -> str:
        if not self.selected_controller:
            raise RuntimeError("No controller selected.")

        events = pygame.event.get()
        inputs = []

        for event in events:
            if event.type == pygame.JOYBUTTONDOWN:
                inputs.append(f"Button {event.button} pressed.")
            elif event.type == pygame.JOYAXISMOTION:
                inputs.append(f"Axis {event.axis} moved to {event.value:.2f}.")
            elif event.type == pygame.JOYHATMOTION:
                inputs.append(f"Hat {event.hat} moved to {event.value}.")

        return "\n".join(inputs)

class WebSocketServer:
    def __init__(self, ip: str, port: int, manager: GameControllerManager):
        self.ip = ip
        self.port = port
        self.manager = manager

    async def _handler(self, websocket, path):
        logging.info(f"Client connected: {path}")
        try:
            while True:
                inputs = self.manager.read_inputs()
                if inputs:
                    await websocket.send(inputs)
                await asyncio.sleep(0.1)
        except websockets.exceptions.ConnectionClosed:
            logging.info("Client disconnected.")

    async def run(self):
        async with websockets.serve(self._handler, self.ip, self.port):
            logging.info(f"WebSocket server started at {self.ip}:{self.port}")
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    manager = GameControllerManager()
    controllers = manager.list_controllers()

    if not controllers:
        logging.info("No controllers found.")
        exit(0)

    logging.info("Available Controllers:")
    for controller in controllers:
        logging.info(controller)

    try:
        selected_index = int(input("Select a controller by index: "))
        manager.select_controller(selected_index)

        server = WebSocketServer(ip="localhost", port=8765, manager=manager)
        asyncio.run(server.run())
    except ValueError:
        logging.error("Invalid input. Please enter a valid index.")
    except RuntimeError as e:
        logging.error(e)
