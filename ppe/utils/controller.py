import math
from abc import ABC, abstractmethod
from typing import Optional, Dict, Set, Literal, Union, Callable, List, Tuple
from dataclasses import dataclass, field
import random
from copy import deepcopy

import pygame

from ppe.engine.common import Body, Vec2, PolygonShape, CircleShape
from ppe.engine.world import World
from ppe.engine.debug import AbstractDebugDrawer
from ppe.utils.view import Camera


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
        """
        A factory method that creates an InputState snapshot from the
        current Pygame input state.
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


class AbstractController(ABC):
    """An abstract base class for all controller strategies."""

    def __init__(self, debug_drawer: Optional[AbstractDebugDrawer] = None):
        """
        Initializes the controller with an optional debug drawer.

        Args:
            debug_drawer: An optional debug drawer for visualizing controller actions.
        """
        self.debug_drawer = debug_drawer

    @property
    @abstractmethod
    def action_description(self) -> str:
        """
        Returns a description of the controller's behavior based on its configuration.
        
        Returns:
            A human-readable string describing what the controller does and how to use it.
        """
        pass

    @abstractmethod
    def update(self, input_state: InputState, dt: float) -> None:
        """
        Performs updates based on the current input state for the frame.

        Args:
            input_state: An object containing the current input state.
            dt: The time step for the frame.
        """
        pass


class ApplicationController(AbstractController):
    """Handles application-level controls like quitting."""

    def __init__(
        self,
        quit_keys: Set[str] = None,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the ApplicationController.

        Args:
            quit_keys: Set of keys that will trigger application quit.
                      Defaults to {"quit", "escape"}.
        """
        super().__init__(debug_drawer)

        self.quit_keys = {"quit", "escape"} if quit_keys is None else quit_keys

        self.should_quit = False

    @property
    def action_description(self) -> str:
        """Returns a description of the controller's behavior."""
        return f"Quit application by pressing one of [{', '.join(sorted(self.quit_keys))}]"

    def update(self, input_state: InputState, dt: float) -> None:
        """Checks for quit conditions."""
        for key in self.quit_keys:
            if key in input_state.keys_pressed:
                self.should_quit = True
                break


class DebugController(AbstractController):
    """Handles debug mode toggling and debug-related functionality."""

    def __init__(
        self,
        controlled_debug_drawer: AbstractDebugDrawer,
        toggle_key: str = "d",
        initial_debug_mode: bool = True,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the DebugController.

        Args:
            controlled_debug_drawer: The debug drawer to control (enable/disable).
            toggle_key: The key to toggle debug mode. Defaults to "d".
            initial_debug_mode: Whether debug mode starts enabled.
            debug_drawer: Optional debug drawer for visualizing this controller's actions.
        """
        super().__init__(debug_drawer)

        self.controlled_debug_drawer = controlled_debug_drawer
        self.toggle_key = toggle_key
        self.debug_mode = initial_debug_mode

        self.controlled_debug_drawer.enabled = self.debug_mode

    @property
    def action_description(self) -> str:
        """Returns a description of the controller's behavior."""
        status = "enabled" if self.debug_mode else "disabled"
        return f"Toggle debug mode (currently {status}) with '{self.toggle_key}' key"

    def update(self, input_state: InputState, dt: float) -> None:
        """Handles debug mode toggling."""
        if self.toggle_key in input_state.keys_pressed:
            self.debug_mode = not self.debug_mode
            self.controlled_debug_drawer.enabled = self.debug_mode


class CameraPanController(AbstractController):
    """Handles camera panning with configurable input methods."""

    def __init__(
        self,
        camera: Camera,
        mode: Literal["keyboard", "mouse", "trackpad"] = "keyboard",
        keys: Tuple[str, str, str, str] = ("up", "down", "left", "right"),
        mouse_button: int = 2,
        speed: float = 5.0,
        trackpad_sensitivity: float = 1.0,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the PanController.

        Args:
            camera: The Camera object to control.
            mode: The input method for panning, either "keyboard", "mouse", or "trackpad".
            keys: A tuple of keys for panning in the order (up, down, left, right).
            mouse_button: The mouse button to use for panning (1=left, 2=middle, 3=right).
            speed: The speed of panning.
            trackpad_sensitivity: The sensitivity for trackpad scroll panning.
        """
        super().__init__(debug_drawer)
        if mode not in ["keyboard", "mouse", "trackpad"]:
            raise ValueError("mode must be either 'keyboard', 'mouse', or 'trackpad'")
        if len(keys) != 4:
            raise ValueError(
                "keys must contain exactly 4 keys in order: [up, down, left, right]"
            )

        self.camera = camera
        self.mode = mode
        self.mouse_button = mouse_button
        self.speed = speed
        self.trackpad_sensitivity = trackpad_sensitivity
        self.keys = keys
        self._last_mouse_pos: Optional[Vec2] = None

    @property
    def action_description(self) -> str:
        """Returns a description of the controller's behavior."""
        if self.mode == "keyboard":
            up, down, left, right = self.keys
            return f"Pan camera with keyboard: {up}/{down} (up/down), {left}/{right} (left/right) at speed {self.speed}"
        elif self.mode == "mouse":
            button_names = {1: "left", 2: "middle", 3: "right"}
            button_name = button_names.get(self.mouse_button, f"button {self.mouse_button}")
            return f"Pan camera by dragging with {button_name} mouse button"
        elif self.mode == "trackpad":
            return f"Pan camera with trackpad scroll gestures (sensitivity: {self.trackpad_sensitivity})"

    def update(self, input_state: InputState, dt: float) -> None:
        """Handles camera panning based on the current input state."""
        if self.mode == "keyboard":
            if self.keys[0] in input_state.keys_held:  # up
                self.camera.position.y += self.speed * dt / self.camera.zoom
            if self.keys[1] in input_state.keys_held:  # down
                self.camera.position.y -= self.speed * dt / self.camera.zoom
            if self.keys[2] in input_state.keys_held:  # left
                self.camera.position.x -= self.speed * dt / self.camera.zoom
            if self.keys[3] in input_state.keys_held:  # right
                self.camera.position.x += self.speed * dt / self.camera.zoom

        elif self.mode == "mouse":
            mouse_button_held = self.mouse_button in input_state.mouse_buttons_held

            if mouse_button_held and self._last_mouse_pos:
                # If currently panning, calculate the delta
                mouse_delta_world = self.camera.screen_to_world(
                    input_state.mouse_position
                ) - self.camera.screen_to_world(self._last_mouse_pos)
                self.camera.position -= mouse_delta_world / self.camera.zoom

            # Update last mouse position for the next frame
            if mouse_button_held:
                self._last_mouse_pos = input_state.mouse_position
            else:
                self._last_mouse_pos = None

        elif self.mode == "trackpad":
            # Trackpad panning using horizontal/vertical scroll gestures
            if input_state.mouse_wheel_delta_x != 0:
                # Horizontal scroll for left/right panning
                pan_x = (
                    input_state.mouse_wheel_delta_x
                    * self.trackpad_sensitivity
                    / self.camera.zoom
                )
                self.camera.position.x -= pan_x

            if input_state.mouse_wheel_delta != 0:
                # Vertical scroll for up/down panning (when not used for zooming)
                pan_y = (
                    input_state.mouse_wheel_delta
                    * self.trackpad_sensitivity
                    / self.camera.zoom
                )
                self.camera.position.y -= pan_y


class CameraZoomController(AbstractController):
    """Handles camera zooming with configurable input methods."""

    def __init__(
        self,
        camera: Camera,
        mode: Literal["mousewheel", "keyboard"] = "mousewheel",
        keys: Tuple[str, str] = ("+", "-"),
        speed: float = 0.5,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the ZoomController.

        Args:
            camera: The Camera object to control.
            mode: The input method for zooming, either "wheel" or "keyboard".
            keys: An optional list to customize keyboard zoom keys.
                  Defaults to ["+", "-"]. Order is [zoom_in, zoom_out].
            speed: The sensitivity of zooming.
        """
        super().__init__(debug_drawer)
        if mode not in ["mousewheel", "keyboard"]:
            raise ValueError("mode must be either 'mousewheel' or 'keyboard'")
        if len(keys) != 2:
            raise ValueError(
                "keys must contain exactly 2 keys in order: [zoom_in, zoom_out]"
            )

        self.camera = camera
        self.mode = mode
        self.speed = speed
        self.keys = keys

    @property
    def action_description(self) -> str:
        """Returns a description of the controller's behavior."""
        if self.mode == "mousewheel":
            return f"Zoom camera with mouse wheel (sensitivity: {self.speed})"
        elif self.mode == "keyboard":
            zoom_in, zoom_out = self.keys
            return f"Zoom camera with keyboard: '{zoom_in}' (zoom in), '{zoom_out}' (zoom out) at speed {self.speed}"

    def update(self, input_state: InputState, dt: float) -> None:
        """Handles camera zooming based on the current input state."""
        if self.mode == "mousewheel":
            # Mouse wheel zooming
            if input_state.mouse_wheel_delta != 0:
                zoom_change = 1 + input_state.mouse_wheel_delta * self.speed
                self.camera.zoom = max(0.1, self.camera.zoom * zoom_change)

        elif self.mode == "keyboard":
            # Keyboard zooming
            if self.keys[0] in input_state.keys_held:  # zoom_in
                zoom_change = 1 + self.speed * dt
                self.camera.zoom = max(0.1, self.camera.zoom * zoom_change)
            if self.keys[1] in input_state.keys_held:  # zoom_out
                zoom_change = 1 - self.speed * dt
                self.camera.zoom = max(0.1, self.camera.zoom * zoom_change)


class BodyDragController(AbstractController):
    """Allows clicking and dragging physics bodies with the mouse."""

    def __init__(
        self,
        world: World,
        camera: Camera,
        mode: Literal["position", "force"] = "force",
        mouse_button: int = 1,
        stiffness: float = 5000.0,
        dragable_bodies: Optional[List[Body]] = None,
        allow_static_bodies: bool = True,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the BodyDragger.

        Args:
            world: The World containing the bodies to drag.
            camera: The Camera for screen-to-world coordinate conversion.
            mode: The dragging mode, either "position" or "force".
            mouse_button: The mouse button to use for dragging (1=left, 2=middle, 3=right).
            stiffness: The spring stiffness for force-based dragging.
            dragable_bodies: Optional list of specific bodies that can be dragged.
                           If None, all bodies in the world are draggable.
            allow_static_bodies: Whether static bodies can be dragged. Static bodies
                               are always moved kinematically regardless of mode.
            debug_drawer: Optional debug drawer for visualizing drag forces.
        """
        super().__init__(debug_drawer)
        self.world = world
        self.camera = camera
        self.stiffness = stiffness
        self.mode = mode
        self.mouse_button = mouse_button
        self.dragable_bodies = dragable_bodies
        self.allow_static_bodies = allow_static_bodies

        self.dragged_body: Optional[Body] = None
        self.grab_point_local: Optional[Vec2] = None

    @property
    def action_description(self) -> str:
        """Returns a description of the controller's behavior."""
        button_names = {1: "left", 2: "middle", 3: "right"}
        button_name = button_names.get(self.mouse_button, f"button {self.mouse_button}")
        
        mode_desc = "kinematically" if self.mode == "position" else f"with spring force (stiffness: {self.stiffness})"
        static_desc = " (including static bodies)" if self.allow_static_bodies else " (dynamic bodies only)"
        
        body_desc = "any body" if self.dragable_bodies is None else f"{len(self.dragable_bodies)} specific bodies"
        
        return f"Drag {body_desc}{static_desc} {mode_desc} using {button_name} mouse button"

    def update(self, input_state: InputState, dt: float) -> None:
        mouse_world_pos = self.camera.screen_to_world(input_state.mouse_position)

        # Check for a new grab
        if (
            self.mouse_button in input_state.mouse_buttons_pressed
        ) and self.dragged_body is None:
            # Determine which bodies to check for dragging
            bodies_to_check = (
                self.dragable_bodies
                if self.dragable_bodies is not None
                else self.world.bodies
            )

            for body in reversed(bodies_to_check):
                # Check if body can be dragged based on mass and settings
                if self.allow_static_bodies or body.inverse_mass != 0.0:
                    if body.is_point_inside(mouse_world_pos):
                        self.dragged_body = body
                        # offset between the mouse position and the body's center/coordinate frame
                        body_position_offset = mouse_world_pos - body.position
                        sin_a, cos_a = math.sin(-body.angle), math.cos(-body.angle)
                        # offset in local coordinates
                        self.grab_point_local = Vec2(
                            body_position_offset.x * cos_a
                            - body_position_offset.y * sin_a,
                            body_position_offset.x * sin_a
                            + body_position_offset.y * cos_a,
                        )
                        break

        # Check for release
        if self.mouse_button in input_state.mouse_buttons_released:
            self.dragged_body = None
            self.grab_point_local = None

        # Apply drag force if a body is being held
        if self.dragged_body:
            # compute the point in world coordinates where the body is grabbed
            # note that this is not necessarily the same as the current mouse position as the body may have moved since the grab
            sin_a, cos_a = math.sin(self.dragged_body.angle), math.cos(
                self.dragged_body.angle
            )
            world_offset = Vec2(
                self.grab_point_local.x * cos_a - self.grab_point_local.y * sin_a,
                self.grab_point_local.x * sin_a + self.grab_point_local.y * cos_a,
            )

            if self.mode == "position" or self.dragged_body.inverse_mass == 0.0:
                # Kinematic: Set the body's position directly
                # Static bodies are always moved kinematically regardless of mode
                self.dragged_body.position = mouse_world_pos - world_offset

            elif self.mode == "force":
                # Dynamic: Apply a spring-like force (only for non-static bodies)
                world_grab_point = self.dragged_body.position + world_offset
                force_dir = mouse_world_pos - world_grab_point
                force = force_dir * self.stiffness

                # Apply force and torque
                self.dragged_body.force_accumulator += force
                torque = world_offset.x * force.y - world_offset.y * force.x
                self.dragged_body.torque_accumulator += torque

                if self.debug_drawer is not None:
                    # Draw debug visualization
                    self.debug_drawer.add_line(
                        start=world_grab_point,
                        end=mouse_world_pos,
                        color=(0, 255, 0),
                        arrow=True,
                    )
                    # Draw the grab point
                    self.debug_drawer.add_marker(
                        position=world_grab_point, color=(0, 255, 0)
                    )


class BodySpawnController(AbstractController):
    """Spawns new bodies on key press."""

    def __init__(
        self,
        world: World,
        camera: Camera,
        mouse_spawn_objects: Dict[int, Union[List[Body], Callable]] = None,
        keyboard_spawn_objects: Dict[str, Union[List[Body], Callable]] = None,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        super().__init__(debug_drawer)

        self.world = world
        self.camera = camera

        self.default_density = 1  # Default density for spawned bodies

        if mouse_spawn_objects is None and keyboard_spawn_objects is None:
            mouse_spawn_objects = {1: self.spawn_box, 3: self.spawn_circle}

        self.mouse_spawn_objects = (
            dict() if mouse_spawn_objects is None else mouse_spawn_objects
        )
        self.keyboard_spawn_objects = (
            dict() if keyboard_spawn_objects is None else keyboard_spawn_objects
        )

    @property
    def action_description(self) -> str:
        """Returns a description of the controller's behavior."""
        descriptions = []
        
        if self.mouse_spawn_objects:
            button_names = {1: "left", 2: "middle", 3: "right"}
            mouse_desc = []
            for button, spawn_option in self.mouse_spawn_objects.items():
                button_name = button_names.get(button, f"button {button}")
                if callable(spawn_option):
                    object_name = spawn_option.__name__.replace("spawn_", "")
                else:
                    object_name = f"{len(spawn_option)} predefined objects"
                mouse_desc.append(f"{button_name} click: {object_name}")
            descriptions.append("Mouse - " + ", ".join(mouse_desc))
        
        if self.keyboard_spawn_objects:
            key_desc = []
            for key, spawn_option in self.keyboard_spawn_objects.items():
                if callable(spawn_option):
                    object_name = spawn_option.__name__.replace("spawn_", "")
                else:
                    object_name = f"{len(spawn_option)} predefined objects"
                key_desc.append(f"'{key}': {object_name}")
            descriptions.append("Keyboard - " + ", ".join(key_desc))
        
        if not descriptions:
            descriptions.append("No spawn bindings configured")
        
        return "Spawn bodies at mouse position: " + "; ".join(descriptions)

    def spawn_circle(self) -> Body:
        """Spawns a circle body at the given position."""
        circle_shape = CircleShape.create_random_circle()
        circle_body = Body(
            shape=circle_shape,
            position=Vec2(0, 0),  # Placeholder position, will be set by the controller
            mass=circle_shape.get_area() * self.default_density,
        )
        return circle_body

    def spawn_box(self) -> Body:
        """Spawns a box body at the given position."""
        box_shape = PolygonShape.create_random_rectangle()
        box_body = Body(
            shape=box_shape,
            position=Vec2(0, 0),  # Placeholder position, will be set by the controller
            mass=box_shape.get_area() * self.default_density,
        )
        return box_body

    def get_new_body(self, spawn_option: Union[List[Body], Callable]) -> Body:
        """Returns a new body based on the spawn option."""
        if not isinstance(spawn_option, list):
            return spawn_option()
        else:
            # Sample a random body from the list and copy it
            return deepcopy(random.choice(spawn_option))

    def update(self, input_state: InputState, dt: float) -> None:
        """Handles spawning bodies based on input state."""
        # Check for button presses
        for button, spawn_option in self.mouse_spawn_objects.items():
            if button in input_state.mouse_buttons_pressed:
                new_body = self.get_new_body(spawn_option)
                new_body.position = self.camera.screen_to_world(
                    input_state.mouse_position
                )
                self.world.add_body(new_body)

        # Check for key presses
        for key, spawn_option in self.keyboard_spawn_objects.items():
            if key in input_state.keys_pressed:
                new_body = self.get_new_body(spawn_option)
                new_body.position = self.camera.screen_to_world(
                    input_state.mouse_position
                )
                self.world.add_body(new_body)


class BodySteeringController(AbstractController):
    """
    A reusable controller for moving and rotating a specific body with
    configurable keys and control modes.
    """

    def __init__(
        self,
        body: Body,
        move_speed: float = 5.0,
        keys: Tuple[str, str, str, str] = ("w", "s", "a", "d"),
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        super().__init__(debug_drawer)

        self.body = body
        self.move_speed = move_speed
        self.keys = keys

    @property
    def action_description(self) -> str:
        """Returns a description of the controller's behavior."""
        up, down, left, right = self.keys
        return f"Control body movement with keys: {up}/{down} (up/down), {left}/{right} (left/right) at speed {self.move_speed}"

    def update(self, input_state: InputState, dt: float) -> None:
        if self.keys[0] in input_state.keys_held:
            self.body.position.y += self.move_speed * dt
        if self.keys[1] in input_state.keys_held:
            self.body.position.y -= self.move_speed * dt
        if self.keys[2] in input_state.keys_held:
            self.body.position.x -= self.move_speed * dt
        if self.keys[3] in input_state.keys_held:
            self.body.position.x += self.move_speed * dt

class HoverRotateController(AbstractController):
    """A controller that rotates a body around its center when the mousewheel is turnd and the mouse is hovering over it."""

    def __init__(
        self,
        world: World,
        camera: Camera,
        rotation_speed: float = 3.0,
        allow_static_bodies: bool = True,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        super().__init__(debug_drawer)

        self.rotation_speed = rotation_speed
        self.world = world
        self.camera = camera
        self.allow_static_bodies = allow_static_bodies

    @property
    def action_description(self) -> str:
        """Returns a description of the controller's behavior."""
        body_desc = "any body" if self.allow_static_bodies else "dynamic bodies only"
        return f"Rotate {body_desc} with mouse wheel when hovering (speed: {self.rotation_speed})"

    def update(self, input_state: InputState, dt: float) -> None:
        bodies = self.world.get_bodies_at_point(
            self.camera.screen_to_world(input_state.mouse_position)
        )
        if not bodies:
            return

        body = bodies[0]
        if not self.allow_static_bodies and body.inverse_mass == 0:
            return
        
        if input_state.mouse_wheel_delta != 0:
            # Rotate the body around its center based on mouse wheel input
            rotation_amount = input_state.mouse_wheel_delta * self.rotation_speed * dt
            body.angle += rotation_amount