import sys

import pygame
from typing import List, Optional
import logging

def configure_console_logger(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

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
        """Load all connected USB game controllers."""
        self.controllers.clear()
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            self.controllers.append(GameController(index=i, name=joystick.get_name()))

    def list_controllers(self) -> List[GameController]:
        """Return a list of available controllers."""
        return self.controllers

    def select_controller(self, index: int) -> None:
        """Select a controller by index."""
        if index < 0 or index >= len(self.controllers):
            raise ValueError("Invalid controller index.")

        joystick = pygame.joystick.Joystick(index)
        joystick.init()
        self.selected_controller = joystick
        logging.info(f"Selected controller: {joystick.get_name()}")

    def log_inputs(self) -> None:
        """Log inputs from the selected controller."""
        if not self.selected_controller:
            raise RuntimeError("No controller selected.")

        logger.info(f"Listening for inputs from {self.selected_controller.get_name()} (Press Ctrl+C to stop)...")
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        logger.info(f"Button {event.button} pressed.")
                    elif event.type == pygame.JOYAXISMOTION:
                        logger.info(f"Axis {event.axis} moved to {event.value:.2f}.")
                    elif event.type == pygame.JOYHATMOTION:
                        logger.info(f"Hat {event.hat} moved to {event.value}.")
        except KeyboardInterrupt:
            logger.info("Exiting input logger...")
        finally:
            pygame.quit()

if __name__ == "__main__":
    configure_console_logger()
    logger = logging.getLogger(__name__)
    
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
        manager.log_inputs()
    except ValueError:
        logger.info("Invalid input. Please enter a valid index.")
    except RuntimeError as e:
        logger.info(e)
