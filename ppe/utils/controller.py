import math
from abc import ABC, abstractmethod
from typing import Optional, Dict, Set, Literal, Union, Callable, List
from dataclasses import dataclass, field
import random
from copy import deepcopy

import pygame

from ppe.engine.common import Body, Vec2, PolygonShape, CircleShape
from ppe.engine.world import World
from ppe.engine.debug import AbstractDebugDrawer
from ppe.utils.view import Camera


@dataclass
class InputState:
    """A generic container for all user input for a single frame."""

    # Continuous State
    mouse_position: Vec2
    mouse_buttons_held: Set[int] = field(default_factory=set)
    keys_held: Set[str] = field(default_factory=set)

    # Single-Frame Events
    mouse_buttons_pressed: Set[int] = field(default_factory=set)
    mouse_buttons_released: Set[int] = field(default_factory=set)
    keys_pressed: Set[str] = field(default_factory=set)
    keys_released: Set[str] = field(default_factory=set)
    mouse_wheel_delta: float = 0.0

    @classmethod
    def from_pygame(cls) -> "InputState":
        """
        A factory method that creates an InputState snapshot from the
        current Pygame input state.
        """
        # 2. Create the instance with continuous state
        instance = cls(
            mouse_position=Vec2(*pygame.mouse.get_pos()),
            mouse_buttons_held={
                button
                for button, pressed in enumerate(pygame.mouse.get_pressed())
                if pressed
            },
            keys_held={
                pygame.key.name(k)
                for k, pressed in enumerate(pygame.key.get_pressed())
                if pressed
            },
        )

        # 3. Process the event queue for single-frame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # pylint: disable=no-member
                instance.keys_pressed.add("quit")
            elif event.type == pygame.MOUSEWHEEL:  # pylint: disable=no-member
                instance.mouse_wheel_delta = event.y
            elif event.type == pygame.KEYDOWN:  # pylint: disable=no-member
                instance.keys_pressed.add(pygame.key.name(event.key))
            elif event.type == pygame.KEYUP:  # pylint: disable=no-member
                instance.keys_released.add(pygame.key.name(event.key))
            elif event.type == pygame.MOUSEBUTTONDOWN:  # pylint: disable=no-member
                instance.mouse_buttons_pressed.add(event.button)
            elif event.type == pygame.MOUSEBUTTONUP:  # pylint: disable=no-member
                instance.mouse_buttons_released.add(event.button)

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

    @abstractmethod
    def update(self, input_state: InputState, dt: float) -> None:
        """
        Performs updates based on the current input state for the frame.

        Args:
            input_state: An object containing the current input state.
            dt: The time step for the frame.
        """
        raise NotImplementedError


class CameraController(AbstractController):
    """Handles camera pan and zoom controls with configurable panning methods."""

    def __init__(
        self,
        camera: Camera,
        pan_mode: Literal["keys", "mouse", None] = "keys",
        pan_keys: Dict[Literal["up", "down", "left", "right"], int] = None,
        pan_speed: float = 300.0,
        zoom_speed: float = 0.1,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the CameraController.

        Args:
            camera: The Camera object to control.
            pan_mode: The method for panning, either "keys" or "mouse".
            pan_keys: An optional dictionary to customize keyboard panning keys.
                      Defaults to WASD. Keys are "up", "down", "left", "right".
            pan_speed: The speed of keyboard panning.
            zoom_speed: The sensitivity of mouse wheel zooming.
        """
        super().__init__(debug_drawer)
        if pan_mode not in ["keys", "mouse"]:
            raise ValueError("pan_mode must be either 'keys' or 'mouse'")

        self.camera = camera
        self.pan_mode = pan_mode
        self.pan_speed = pan_speed
        self.zoom_speed = zoom_speed

        if self.pan_mode == "keys":
            if pan_keys is None:
                # Default to WASD if no custom keys are provided
                self.pan_keys = {
                    "up": pygame.K_w,  # pylint:disable=no-member
                    "down": pygame.K_s,  # pylint:disable=no-member
                    "left": pygame.K_a,  # pylint:disable=no-member
                    "right": pygame.K_d,  # pylint:disable=no-member
                }
            else:
                if set(pan_keys.keys()) != {"up", "down", "left", "right"}:
                    raise ValueError(
                        "pan_keys must contain 'up', 'down', 'left', and 'right' keys"
                    )
                self.pan_keys = pan_keys
        elif self.pan_mode == "mouse":
            self._last_mouse_pos: Optional[Vec2] = None
        elif self.pan_mode is None:
            pass
        else:
            raise ValueError("Invalid pan_mode. Must be 'keys', 'mouse', or None.")

    def update(self, input_state: InputState, dt: float) -> None:
        """Handles all camera controls based on the current input state."""
        # Zooming (always active)
        if input_state.mouse_wheel_delta != 0:
            zoom_change = 1 + input_state.mouse_wheel_delta * self.zoom_speed
            self.camera.zoom = max(0.1, self.camera.zoom * zoom_change)

        # --- Keyboard Panning ---
        if self.pan_mode == "keys":
            if self.pan_keys["up"] in input_state.keys_held:
                self.camera.position.y -= self.pan_speed * dt / self.camera.zoom
            if self.pan_keys["down"] in input_state.keys_held:
                self.camera.position.y += self.pan_speed * dt / self.camera.zoom
            if self.pan_keys["left"] in input_state.keys_held:
                self.camera.position.x -= self.pan_speed * dt / self.camera.zoom
            if self.pan_keys["right"] in input_state.keys_held:
                self.camera.position.x += self.pan_speed * dt / self.camera.zoom

        # --- Mouse Panning ---
        elif self.pan_mode == "mouse":
            middle_mouse_held = 1 in input_state.mouse_buttons_held

            if middle_mouse_held and self._last_mouse_pos:
                # If currently panning, calculate the delta
                mouse_delta_world = self.camera.screen_to_world(
                    input_state.mouse_position
                ) - self.camera.screen_to_world(self._last_mouse_pos)
                self.camera.position -= mouse_delta_world / self.camera.zoom

            # Update last mouse position for the next frame
            if middle_mouse_held:
                self._last_mouse_pos = input_state.mouse_position
            else:
                self._last_mouse_pos = None


class BodyDragger(AbstractController):
    """Allows clicking and dragging physics bodies with the mouse."""

    def __init__(
        self,
        world: World,
        camera: Camera,
        drag_mode: Literal["position", "force"] = "force",
        stiffness: float = 5000.0,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        super().__init__(debug_drawer)
        self.world = world
        self.camera = camera
        self.stiffness = stiffness
        self.drag_mode = drag_mode

        self.dragged_body: Optional[Body] = None
        self.grab_point_local: Optional[Vec2] = None

    def update(self, input_state: InputState, dt: float) -> None:
        mouse_world_pos = self.camera.screen_to_world(input_state.mouse_position)

        # Check for a new grab
        if (0 in input_state.mouse_buttons_pressed) and self.dragged_body is None:
            for body in reversed(self.world.bodies):
                if body.inverse_mass != 0.0 and body.is_point_inside(mouse_world_pos):
                    self.dragged_body = body
                    # offset between the mouse position and the body's center/coordinate frame
                    body_position_offset = mouse_world_pos - body.position
                    sin_a, cos_a = math.sin(-body.angle), math.cos(-body.angle)
                    # offset in local coordinates
                    self.grab_point_local = Vec2(
                        body_position_offset.x * cos_a - body_position_offset.y * sin_a,
                        body_position_offset.x * sin_a + body_position_offset.y * cos_a,
                    )
                    break

        # Check for release
        if not 1 in input_state.mouse_buttons_released:
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

            if self.drag_mode == "position":
                # Kinematic: Set the body's position directly
                self.dragged_body.position = mouse_world_pos - world_offset

            elif self.drag_mode == "force":
                # Dynamic: Apply a spring-like force
                world_grab_point = self.dragged_body.position + world_offset
                force_dir = mouse_world_pos - world_grab_point
                force = force_dir * self.stiffness

                # Apply force and torque
                self.dragged_body.force_accumulator += force
                torque = world_offset.x * force.y - world_offset.y * force.x
                self.dragged_body.torque_accumulator += torque

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


class BodySpawner(AbstractController):
    """Spawns new bodies on key press."""

    def __init__(
        self,
        world: World,
        camera: Camera,
        button_spawn_objects: Dict[str, Union[List[Body], Callable]] = None,
        key_spawn_objects: Dict[int, Union[List[Body], Callable]] = None,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        super().__init__(debug_drawer)

        self.world = world
        self.camera = camera

        self.default_density = 1  # Default density for spawned bodies

        if button_spawn_objects is None:
            self.button_spawn_objects = {}
        if key_spawn_objects is None:
            self.key_spawn_objects = {0: self.spawn_box, 2: self.spawn_circle}

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
        for button, spawn_option in self.button_spawn_objects.items():
            if button in input_state.mouse_buttons_pressed:
                new_body = self.get_new_body(spawn_option)
                new_body.position = self.camera.screen_to_world(
                    input_state.mouse_position
                )
                self.world.add_body(new_body)

        # Check for key presses
        for key, spawn_option in self.key_spawn_objects.items():
            if key in input_state.keys_pressed:
                new_body = self.get_new_body(spawn_option)
                new_body.position = self.camera.screen_to_world(
                    input_state.mouse_position
                )
                self.world.add_body(new_body)


class BodyMovementController(AbstractController):
    """
    A reusable controller for moving and rotating a specific body with
    configurable keys and control modes.
    """

    def __init__(
        self,
        is_body_selectable: bool = True,
        body: Optional[Body] = None,
        world: Optional[World] = None,
        camera: Optional[Camera] = None,
        control_mode: Literal["position", "dynamic"] = "position",
        move_speed: float = 150.0,
        rotation_speed: float = math.pi,
        key_bindings: Dict[
            Literal["up", "down", "left", "right", "rotate_cw", "rotate_ccw"], str
        ] = None,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the controller.

        Args:
            body: The specific Body instance to control.
            control_mode: "position" to control position directly, or
                          "dynamic" to control velocity.
            move_speed: The speed of linear movement.
            rotation_speed: The speed of angular rotation in radians per second.
            key_bindings: Optional dictionary to override default keys.
                          Keys are "up", "down", "left", "right",
                          "rotate_cw", "rotate_ccw".
        """
        super().__init__(debug_drawer)

        if control_mode not in ["position", "dynamic"]:
            raise ValueError("control_mode must be 'position' or 'dynamic'")
        if not is_body_selectable and body is None:
            raise ValueError(
                "If is_body_selectable is False, a body must be provided to control."
            )
        if is_body_selectable and (world is None or camera is None):
            raise ValueError(
                "If is_body_selectable is True, both world and camera must be provided."
            )

        self.is_body_selectable = is_body_selectable
        self.camera = camera
        self.world = world
        self.body = body
        self.control_mode = control_mode
        self.move_speed = move_speed
        self.rotation_speed = rotation_speed

        # Set default key bindings if none are provided
        if key_bindings is None:
            self.key_bindings = {
                "up": "w",
                "down": "s",
                "left": "a",
                "right": "d",
                "rotate_ccw": "q",
                "rotate_cw": "e",
            }
        else:
            self.key_bindings = key_bindings

    def update(self, input_state: InputState, dt: float) -> None:
        """Updates the controlled body based on held keys."""
        if self.is_body_selectable:
            if 0 in input_state.mouse_buttons_pressed:
                self.body = None  # Deselect by default

                # select the new body if there is one under the mouse
                mouse_world_pos = self.camera.screen_to_world(
                    input_state.mouse_position
                )
                for body in reversed(self.world.bodies):
                    if body.inverse_mass != 0.0 and body.is_point_inside(
                        mouse_world_pos, body.position, body.angle
                    ):
                        self.body = body
                        break

        if self.body is None:
            return

        if self.control_mode == "position":
            # Direct position manipulation
            if self.key_bindings["up"] in input_state.keys_held:
                self.body.position.y -= self.move_speed * dt
            if self.key_bindings["down"] in input_state.keys_held:
                self.body.position.y += self.move_speed * dt
            if self.key_bindings["left"] in input_state.keys_held:
                self.body.position.x -= self.move_speed * dt
            if self.key_bindings["right"] in input_state.keys_held:
                self.body.position.x += self.move_speed * dt

            # Direct angle manipulation
            if self.key_bindings["rotate_ccw"] in input_state.keys_held:
                self.body.angle -= self.rotation_speed * dt
            if self.key_bindings["rotate_cw"] in input_state.keys_held:
                self.body.angle += self.rotation_speed * dt

        elif self.control_mode == "dynamic":
            # Dynamic control by setting velocity
            linear_velocity = Vec2(0, 0)
            if self.key_bindings["up"] in input_state.keys_held:
                linear_velocity.y -= self.move_speed
            if self.key_bindings["down"] in input_state.keys_held:
                linear_velocity.y += self.move_speed
            if self.key_bindings["left"] in input_state.keys_held:
                linear_velocity.x -= self.move_speed
            if self.key_bindings["right"] in input_state.keys_held:
                linear_velocity.x += self.move_speed

            self.body.velocity = linear_velocity

            # Dynamic control by setting angular velocity
            angular_velocity = 0.0
            if self.key_bindings["rotate_ccw"] in input_state.keys_held:
                angular_velocity -= self.rotation_speed
            if self.key_bindings["rotate_cw"] in input_state.keys_held:
                angular_velocity += self.rotation_speed

            self.body.angular_velocity = angular_velocity


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
        world: World,
        debug_drawer: AbstractDebugDrawer,
        toggle_key: str = "d",
        initial_debug_mode: bool = True,
    ):
        """
        Initializes the DebugController.

        Args:
            world: The World instance to control debug drawing for.
            debug_drawer: The debug drawer to use for rendering debug information.
            toggle_key: The key to toggle debug mode. Defaults to "d".
            initial_debug_mode: Whether debug mode starts enabled.
        """
        super().__init__(debug_drawer)

        self.world = world
        self.toggle_key = toggle_key
        self.debug_mode = initial_debug_mode

        # Set the world's debug drawer and configure its initial state
        self.world.debug_drawer = self.debug_drawer
        self.debug_drawer.enabled = self.debug_mode

    def update(self, input_state: InputState, dt: float) -> None:
        """Handles debug mode toggling."""
        if self.toggle_key in input_state.keys_pressed:
            self.debug_mode = not self.debug_mode
            self.debug_drawer.enabled = self.debug_mode
