from typing import Set
from dataclasses import dataclass, field

import pygame

from ppe.engine.common import Vec2

PYGAME_KEY_CONSTANTS = [
    getattr(pygame, key_name) for key_name in dir(pygame) if key_name.startswith("K_")
]


@dataclass
class InputState:
    """A generic container for all user input for a single frame."""

    # Continuous State
    mouse_position: Vec2
    # mouse buttons are 1 (left), 2 (middle), 3 (right)
    mouse_buttons_held: Set[int] = field(default_factory=set)
    keys_held: Set[str] = field(default_factory=set)

    # Single-Frame Events
    mouse_buttons_pressed: Set[int] = field(default_factory=set)
    mouse_buttons_released: Set[int] = field(default_factory=set)
    keys_pressed: Set[str] = field(default_factory=set)
    keys_released: Set[str] = field(default_factory=set)
    mouse_wheel_delta: float = 0.0
    mouse_wheel_delta_x: float = 0.0  # Horizontal scroll for trackpad panning

    @classmethod
    def from_pygame(cls) -> "InputState":
        """Create an InputState snapshot from the current Pygame input state.

        This method polls Pygame for the current state of the mouse and keyboard,
        including which buttons and keys are held down, and processes the event
        queue to capture single-frame events like key presses and releases.

        Returns:
            InputState: An instance of InputState populated with the current input data.
        """
        # get the held keys. note the caveats documented at https://www.pygame.org/docs/ref/key.html
        key_states = pygame.key.get_pressed()
        held_keys = {pygame.key.name(k) for k in PYGAME_KEY_CONSTANTS if key_states[k]}

        # get the held mouse buttons. we add 1 to the button index to match Pygame's button numbering in the event system
        # 1 is left, 2 is middle, 3 is right
        mouse_button_states = pygame.mouse.get_pressed()
        held_mouse_buttons = {
            button + 1 for button, pressed in enumerate(mouse_button_states) if pressed
        }

        # Process the event queue for single-frame events
        keys_pressed = set()
        keys_released = set()
        mouse_buttons_pressed = set()
        mouse_buttons_released = set()
        mouse_wheel_delta = 0.0
        mouse_wheel_delta_x = 0.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # pylint: disable=no-member
                keys_pressed.add("quit")
            elif event.type == pygame.MOUSEWHEEL:  # pylint: disable=no-member
                mouse_wheel_delta += event.y
                # Capture horizontal scroll if available (for trackpad panning)
                if hasattr(event, "x"):
                    mouse_wheel_delta_x += event.x
            elif event.type == pygame.KEYDOWN:  # pylint: disable=no-member
                keys_pressed.add(pygame.key.name(event.key))
            elif event.type == pygame.KEYUP:  # pylint: disable=no-member
                keys_released.add(pygame.key.name(event.key))
            elif event.type == pygame.MOUSEBUTTONDOWN:  # pylint: disable=no-member
                mouse_buttons_pressed.add(event.button)
            elif event.type == pygame.MOUSEBUTTONUP:  # pylint: disable=no-member
                mouse_buttons_released.add(event.button)

        # Create the InputState instance
        instance = cls(
            mouse_position=Vec2(*pygame.mouse.get_pos()),
            mouse_buttons_held=held_mouse_buttons,
            mouse_buttons_pressed=mouse_buttons_pressed,
            mouse_buttons_released=mouse_buttons_released,
            keys_held=held_keys,
            keys_pressed=keys_pressed,
            keys_released=keys_released,
            mouse_wheel_delta=mouse_wheel_delta,
            mouse_wheel_delta_x=mouse_wheel_delta_x,
        )

        return instance
