"""A collection of controllers for handling user input in a physics simulation.

This module provides a flexible controller system for managing user interactions to actions
in the simulation. Note that controllers could be interpreted as a special case of widgets
where no rendering is done. However, we still have them seperate as they serve slightly
different purposes.

The available controllers include:
- `ApplicationController`: Handles application-level actions like quitting.
- `DebugController`: Toggles debug visualizations.
- `CameraPanController`: Manages camera movement (panning) via keyboard, mouse, or trackpad.
- `CameraZoomController`: Manages camera zoom via mouse wheel or keyboard.
- `BodyDragController`: Allows users to click and drag physics bodies.
- `BodySpawnController`: Spawns new physics bodies based on user input.
- `BodySteeringController`: Provides direct keyboard control over a specific body.
- `HoverRotateController`: Rotates a body when the mouse hovers over it and the scroll
    wheel is used.

These controllers are designed to be modular and configurable, allowing for easy
customization of user controls in different simulation scenarios.
"""

import math
import random
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Callable, Dict, List, Literal, Optional, Set, Tuple, Union

from ppe.engine.common import Body, Vec2
from ppe.engine.debug import DebugRecorder
from ppe.engine.world import World
from ppe.frontend.input import InputState
from ppe.frontend.view import Camera


class AbstractController(ABC):
    """An abstract base class for all controller strategies."""

    def __init__(self, debug_recorder: Optional[DebugRecorder] = None):
        """
        Initializes the controller with an optional debug drawer.

        Args:
            debug_recorder: An optional debug drawer for visualizing controller actions.
        """
        self.debug_recorder = debug_recorder

    @property
    @abstractmethod
    def action_description(self) -> str:
        """
        Returns a description of the controller's behavior based on its configuration.

        Returns:
            str: A human-readable string describing what the controller does and how to use it.
        """
        pass

    @abstractmethod
    def update(self, input_state: InputState, dt: float) -> None:
        """
        Performs updates based on the current input state for the frame.

        Args:
            input_state (InputState): An object containing the current input state.
            dt (float): The time step for the frame.
        """
        pass


class ApplicationController(AbstractController):
    """Handles application-level controls like quitting.

    This controller monitors for specific key presses that signal the user's
    intent to close the application. When one of the designated quit keys is
    pressed, it sets a flag that the main application loop can check to
    initiate a clean shutdown.
    """

    def __init__(
        self,
        quit_keys: Set[str] = None,
        debug_recorder: Optional[DebugRecorder] = None,
    ):
        """Initialize the ApplicationController.

        Args:
            quit_keys (Set[str]): A set of key names that will trigger the application
                to quit. Defaults to {"quit", "escape"}. The "quit" key corresponds
                to the window's close button.
            debug_recorder (Optional[DebugRecorder]): An optional debug drawer for
                visualizing controller actions.
        """
        super().__init__(debug_recorder)

        self.quit_keys = {"quit", "escape"} if quit_keys is None else quit_keys

        self.should_quit = False

    @property
    def action_description(self) -> str:
        """Return a description of the controller's behavior.

        Returns:
            (str): A human-readable string describing how to quit the application.
        """
        return (
            f"Quit application by pressing one of [{', '.join(sorted(self.quit_keys))}]"
        )

    def update(self, input_state: InputState, dt: float) -> None:
        """Check for quit conditions and update the should_quit flag.

        Args:
            input_state (InputState): The current input state for the frame.
            dt (float): The time step for the frame.
        """
        for key in self.quit_keys:
            if key in input_state.keys_pressed:
                self.should_quit = True
                break


class DebugController(AbstractController):
    """Handles debug mode toggling and debug-related functionality.

    This controller allows the user to toggle a debug visualization layer on and
    off by pressing a designated key. It directly controls the `enabled` state
    of a given debug drawer instance.
    """

    def __init__(
        self,
        controlled_debug_recorder: DebugRecorder,
        toggle_key: str = "d",
        initial_debug_mode: bool = True,
        debug_recorder: Optional[DebugRecorder] = None,
    ):
        """Initialize the DebugController.

        Args:
            controlled_debug_recorder (DebugRecorder): The debug drawer instance
                to be controlled (e.g., enabled or disabled).
            toggle_key (str): The key used to toggle the debug mode. Defaults to "d".
            initial_debug_mode (bool): The initial state of the debug mode.
                Defaults to True (enabled).
            debug_recorder (Optional[DebugRecorder]): An optional debug drawer for
                visualizing this controller's own actions.
        """
        super().__init__(debug_recorder)

        self.controlled_debug_recorder = controlled_debug_recorder
        self.toggle_key = toggle_key
        self.debug_mode = initial_debug_mode

        self.controlled_debug_recorder.enabled = self.debug_mode

    @property
    def action_description(self) -> str:
        """Return a description of the controller's behavior.

        Returns:
            (str): A human-readable string describing how to toggle debug mode.
        """
        status = "enabled" if self.debug_mode else "disabled"
        return f"Toggle debug mode (currently {status}) with '{self.toggle_key}' key"

    def update(self, input_state: InputState, dt: float) -> None:
        """Toggle debug mode if the designated key is pressed.

        Args:
            input_state (InputState): The current input state for the frame.
            dt (float): The time step for the frame.
        """
        if self.toggle_key in input_state.keys_pressed:
            self.debug_mode = not self.debug_mode
            self.controlled_debug_recorder.enabled = self.debug_mode


class CameraPanController(AbstractController):
    """Handles camera panning with configurable input methods.

    This controller allows the user to move the camera's viewpoint horizontally
    and vertically. It supports three modes of operation:
    - "keyboard": Uses arrow keys or custom keys to pan.
    - "mouse": Drags the view by holding a specific mouse button.
    - "trackpad": Uses horizontal and vertical scroll gestures, common on trackpads.
    """

    def __init__(
        self,
        camera: Camera,
        mode: Literal["keyboard", "mouse", "trackpad"] = "keyboard",
        keys: Tuple[str, str, str, str] = ("up", "down", "left", "right"),
        mouse_button: int = 2,
        speed: float = 5.0,
        trackpad_sensitivity: float = 1.0,
        debug_recorder: Optional[DebugRecorder] = None,
    ):
        """Initialize the CameraPanController.

        Args:
            camera (Camera): The camera object to be controlled.
            mode (Literal["keyboard", "mouse", "trackpad"]): The input method for panning.
                Defaults to "keyboard".
            keys (Tuple[str, str, str, str]): A tuple of key names for panning, in the
                order (up, down, left, right). Defaults to ("up", "down", "left", "right").
            mouse_button (int): The mouse button to use for drag-panning (1=left, 2=middle,
                3=right). Defaults to 2 (middle).
            speed (float): The speed of keyboard-based panning. Defaults to 5.0.
            trackpad_sensitivity (float): The sensitivity multiplier for trackpad scroll
                panning. Defaults to 1.0.
            debug_recorder (Optional[DebugRecorder]): An optional debug drawer for
                visualizing controller actions.
        """
        super().__init__(debug_recorder)
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
        """Return a description of the controller's behavior.

        Returns:
            (str): A human-readable string describing the currently active panning controls.
        """
        if self.mode == "keyboard":
            up, down, left, right = self.keys
            return f"Pan camera with keyboard: {up}/{down} (up/down), {left}/{right} (left/right) at speed {self.speed}"
        elif self.mode == "mouse":
            button_names = {1: "left", 2: "middle", 3: "right"}
            button_name = button_names.get(
                self.mouse_button, f"button {self.mouse_button}"
            )
            return f"Pan camera by dragging with {button_name} mouse button"
        elif self.mode == "trackpad":
            return f"Pan camera with trackpad scroll gestures (sensitivity: {self.trackpad_sensitivity})"

    def update(self, input_state: InputState, dt: float) -> None:
        """Update the camera's position based on the current input state.

        Args:
            input_state (InputState): The current input state for the frame.
            dt (float): The time step for the frame.
        """
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
    """Handles camera zooming with configurable input methods.

    This controller adjusts the camera's zoom level. It supports two modes:
    - "mousewheel": Uses the mouse wheel to zoom in and out.
    - "keyboard": Uses designated keys to zoom in and out.
    """

    def __init__(
        self,
        camera: Camera,
        mode: Literal["mousewheel", "keyboard"] = "mousewheel",
        keys: Tuple[str, str] = ("+", "-"),
        speed: float = 0.5,
        debug_recorder: Optional[DebugRecorder] = None,
    ):
        """Initialize the CameraZoomController.

        Args:
            camera (Camera): The camera object to be controlled.
            mode (Literal["mousewheel", "keyboard"]): The input method for zooming.
                Defaults to "mousewheel".
            keys (Tuple[str, str]): A tuple of key names for zooming, in the order
                [zoom_in, zoom_out]. Defaults to ("+", "-").
            speed (float): The sensitivity or speed of zooming. Defaults to 0.5.
            debug_recorder (Optional[DebugRecorder]): An optional debug drawer for
                visualizing controller actions.
        """
        super().__init__(debug_recorder)
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
        """Return a description of the controller's behavior.

        Returns:
            (str): A human-readable string describing the currently active zoom controls.
        """
        if self.mode == "mousewheel":
            return f"Zoom camera with mouse wheel (sensitivity: {self.speed})"
        elif self.mode == "keyboard":
            zoom_in, zoom_out = self.keys
            return f"Zoom camera with keyboard: '{zoom_in}' (zoom in), '{zoom_out}' (zoom out) at speed {self.speed}"

    def update(self, input_state: InputState, dt: float) -> None:
        """Update the camera's zoom level based on the current input state.

        Args:
            input_state (InputState): The current input state for the frame.
            dt (float): The time step for the frame.
        """
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
    """Allows clicking and dragging physics bodies with the mouse.

    This controller enables direct manipulation of physics bodies. It can operate
    in two modes:
    - "position": The body's position is kinematically moved to follow the mouse cursor.
      This is a hard constraint and ignores physics.
    - "force": A spring-like force is applied to pull the body towards the mouse
      cursor, allowing for more dynamic and physically-based interactions.

    Static bodies, if draggable, are always moved kinematically.
    """

    def __init__(
        self,
        world: World,
        camera: Camera,
        mode: Literal["position", "force"] = "force",
        mouse_button: int = 1,
        stiffness: float = 5000.0,
        dragable_bodies: Optional[List[Body]] = None,
        allow_static_bodies: bool = True,
        debug_recorder: Optional[DebugRecorder] = None,
    ):
        """Initialize the BodyDragController.

        Args:
            world (World): The physics world containing the bodies.
            camera (Camera): The camera for converting screen to world coordinates.
            mode (Literal["position", "force"]): The dragging mode. Defaults to "force".
            mouse_button (int): The mouse button used for dragging (1=left, 2=middle,
                3=right). Defaults to 1 (left).
            stiffness (float): The stiffness of the spring force in "force" mode.
                Defaults to 5000.0.
            dragable_bodies (Optional[List[Body]]): A specific list of bodies that can
                be dragged. If None, any body in the world is draggable. Defaults to None.
            allow_static_bodies (bool): Whether static bodies (mass=0) can be dragged.
                Defaults to True.
            debug_recorder (Optional[DebugRecorder]): An optional debug drawer for
                visualizing the drag force.
        """
        super().__init__(debug_recorder)
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
        """Return a description of the controller's behavior.

        Returns:
            (str): A human-readable string describing how to drag bodies.
        """
        button_names = {1: "left", 2: "middle", 3: "right"}
        button_name = button_names.get(self.mouse_button, f"button {self.mouse_button}")

        mode_desc = (
            "kinematically"
            if self.mode == "position"
            else f"with spring force (stiffness: {self.stiffness})"
        )
        static_desc = (
            " (including static bodies)"
            if self.allow_static_bodies
            else " (dynamic bodies only)"
        )

        body_desc = (
            "any body"
            if self.dragable_bodies is None
            else f"{len(self.dragable_bodies)} specific bodies"
        )

        return f"Drag {body_desc}{static_desc} {mode_desc} using {button_name} mouse button"

    def update(self, input_state: InputState, dt: float) -> None:
        """Handle the logic for grabbing, dragging, and releasing bodies.

        Args:
            input_state (InputState): The current input state for the frame.
            dt (float): The time step for the frame.
        """
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
            sin_a, cos_a = (
                math.sin(self.dragged_body.angle),
                math.cos(self.dragged_body.angle),
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

                if self.debug_recorder is not None:
                    # Draw debug visualization
                    self.debug_recorder.add_line(
                        start=world_grab_point,
                        end=mouse_world_pos,
                        color=(0, 255, 0),
                        arrow=True,
                    )
                    # Draw the grab point
                    self.debug_recorder.add_marker(
                        position=world_grab_point, color=(0, 255, 0)
                    )


class BodySpawnController(AbstractController):
    """Spawns new bodies into the world based on user input.

    This controller allows for the creation of new physics bodies at the current
    mouse position. Spawning can be triggered by mouse clicks or key presses.
    The type of body to spawn can be a specific list of predefined bodies or
    generated by a callable function.
    The body gets added to the world instance via the add_body() method.
    """

    def __init__(
        self,
        world: World,
        camera: Camera,
        mouse_spawn_objects: Dict[int, Union[List[Body], Callable]] = None,
        keyboard_spawn_objects: Dict[str, Union[List[Body], Callable]] = None,
        spawn_object_at_mouse_position: Optional[bool] = True,
        debug_recorder: Optional[DebugRecorder] = None,
    ):
        """Initialize the BodySpawnController.

        If no spawn objects are provided, it defaults to spawning a box on left-click
        and a circle on right-click.

        Args:
            world (World): The physics world where bodies will be added.
            camera (Camera): The camera for converting screen to world coordinates.
            mouse_spawn_objects (Dict[int, Union[List[Body], Callable]]): A dictionary
                mapping mouse buttons (1=left, 2=middle, 3=right) to either a list
                of Body objects to choose from or a callable that returns a new Body.
            keyboard_spawn_objects (Dict[str, Union[List[Body], Callable]]): A dictionary
                mapping key names to either a list of Body objects or a callable that
                returns a new Body.
            spawn_object_at_mouse_position (Optional[bool]): Whether to spawn the object at the
                current mouse position. If set the bodies position value will be overridden
                with the mouse position before the body is added to the world. Defaults to True.
            debug_recorder (Optional[DebugRecorder]): An optional debug drawer.
        """
        super().__init__(debug_recorder)

        self.world = world
        self.camera = camera

        self.spawn_object_at_mouse_position = spawn_object_at_mouse_position

        if mouse_spawn_objects is None and keyboard_spawn_objects is None:
            raise ValueError("At least one spawn object source must be provided.")

        self.mouse_spawn_objects = (
            dict() if mouse_spawn_objects is None else mouse_spawn_objects
        )
        self.keyboard_spawn_objects = (
            dict() if keyboard_spawn_objects is None else keyboard_spawn_objects
        )

    @property
    def action_description(self) -> str:
        """Return a description of the controller's behavior.

        Returns:
            (str): A human-readable string describing the configured spawn bindings.
        """
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

    def get_new_body(self, spawn_option: Union[List[Body], Callable]) -> Body:
        """Generate a new body based on the provided spawn option.

        If the option is a callable, it is called to produce a new body.
        If the option is a list, a random body is chosen from the list and
        a deep copy is returned.

        Args:
            spawn_option (Union[List[Body], Callable]): The source for the new body.

        Returns:
            (Body): The newly generated body instance.
        """
        if not isinstance(spawn_option, list):
            return spawn_option()
        else:
            # Sample a random body from the list and copy it
            return deepcopy(random.choice(spawn_option))

    def update(self, input_state: InputState, dt: float) -> None:
        """Check for spawn triggers and add new bodies to the world.

        Args:
            input_state (InputState): The current input state for the frame.
            dt (float): The time step for the frame.
        """
        # Check for button presses
        bodies_to_spawn = []
        for button, spawn_option in self.mouse_spawn_objects.items():
            if button in input_state.mouse_buttons_pressed:
                bodies_to_spawn.append(self.get_new_body(spawn_option))

        # Check for key presses
        for key, spawn_option in self.keyboard_spawn_objects.items():
            if key in input_state.keys_pressed:
                bodies_to_spawn.append(self.get_new_body(spawn_option))

        for body in bodies_to_spawn:
            if self.spawn_object_at_mouse_position:
                position = self.camera.screen_to_world(input_state.mouse_position)
                body.position = position
                body.previous_position = position
            self.world.add_body(body)


class BodySteeringController(AbstractController):
    """A controller for moving a specific body with keyboard inputs.

    This provides simple kinematic control over a single body's position,
    allowing it to be moved up, down, left, or right using a configurable
    set of keys.
    """

    def __init__(
        self,
        body: Body,
        move_speed: float = 5.0,
        keys: Tuple[str, str, str, str] = ("w", "s", "a", "d"),
        debug_recorder: Optional[DebugRecorder] = None,
    ):
        """Initialize the BodySteeringController.

        Args:
            body (Body): The specific body instance to be controlled.
            move_speed (float): The speed at which the body moves. Defaults to 5.0.
            keys (Tuple[str, str, str, str]): A tuple of key names for movement, in the
                order (up, down, left, right). Defaults to ("w", "s", "a", "d").
            debug_recorder (Optional[DebugRecorder]): An optional debug drawer.
        """
        super().__init__(debug_recorder)

        self.body = body
        self.move_speed = move_speed
        self.keys = keys

    @property
    def action_description(self) -> str:
        """Return a description of the controller's behavior.

        Returns:
            (str): A human-readable string describing the movement controls.
        """
        up, down, left, right = self.keys
        return f"Control body movement with keys: {up}/{down} (up/down), {left}/{right} (left/right) at speed {self.move_speed}"

    def update(self, input_state: InputState, dt: float) -> None:
        """Update the body's position based on keyboard input.

        Args:
            input_state (InputState): The current input state for the frame.
            dt (float): The time step for the frame.
        """
        if self.keys[0] in input_state.keys_held:
            self.body.position.y += self.move_speed * dt
        if self.keys[1] in input_state.keys_held:
            self.body.position.y -= self.move_speed * dt
        if self.keys[2] in input_state.keys_held:
            self.body.position.x -= self.move_speed * dt
        if self.keys[3] in input_state.keys_held:
            self.body.position.x += self.move_speed * dt


class HoverRotateController(AbstractController):
    """Rotates a body when the mouse is hovering over it and the wheel is scrolled.

    This controller identifies the topmost body under the mouse cursor and rotates
    it around its center if the mouse wheel is used. This provides a quick way
    to interactively adjust the orientation of bodies in the simulation.
    """

    def __init__(
        self,
        world: World,
        camera: Camera,
        rotation_speed: float = 3.0,
        allow_static_bodies: bool = True,
        debug_recorder: Optional[DebugRecorder] = None,
    ):
        """Initialize the HoverRotateController.

        Args:
            world (World): The physics world containing the bodies.
            camera (Camera): The camera for converting screen to world coordinates.
            rotation_speed (float): A multiplier for the rotation amount.
                Defaults to 3.0.
            allow_static_bodies (bool): Whether static bodies can be rotated.
                Defaults to True.
            debug_recorder (Optional[DebugRecorder]): An optional debug drawer.
        """
        super().__init__(debug_recorder)

        self.rotation_speed = rotation_speed
        self.world = world
        self.camera = camera
        self.allow_static_bodies = allow_static_bodies

    @property
    def action_description(self) -> str:
        """Return a description of the controller's behavior.

        Returns:
            (str): A human-readable string describing how to rotate bodies.
        """
        body_desc = "any body" if self.allow_static_bodies else "dynamic bodies only"
        return f"Rotate {body_desc} with mouse wheel when hovering (speed: {self.rotation_speed})"

    def update(self, input_state: InputState, dt: float) -> None:
        """Check for hover and mouse wheel input, and rotate the body accordingly.

        Args:
            input_state (InputState): The current input state for the frame.
            dt (float): The time step for the frame.
        """
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
