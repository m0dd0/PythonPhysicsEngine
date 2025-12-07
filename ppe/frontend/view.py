"""
This module contains classes for visualizing physics simulations.

The `View` class is an abstract base class for all visualization classes.
It provides a standardized interface for visualizing physics simulations, including
methods for drawing bodies, joints, and other simulation elements.

The available visualization classes are:
- `PygameView`: A visualization class using PyGame.

Besides the `View` class, this module also contains the `Camera` class,
which is responsible for converting between world coordinates and screen coordinates.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import pygame

from ppe.engine.body import Body
from ppe.engine.common import Vec2
from ppe.engine.shapes import CircleShape, PolygonShape


# TODO consider moving Camera to a separate module
class Camera:
    """
    A 2D camera for rendering the game world. A camera object is responsible for
    converting between world coordinates and screen coordinates. Essentially it determines
    which part of the world is visible on the screen.
    """

    def __init__(
        self,
        screen_width: int,  # in pixels
        screen_height: int,  # in pixels
        position: Optional[Vec2] = None,
        zoom: float = 1.0,
        pixels_per_meter: float = 100.0,
    ):
        """
        Initializes a 2D Camera.

        Args:
            screen_width (int): The width of the screen in pixels.
            screen_height (int): The height of the screen in pixels.
            position (Vec2, optional): The initial position of the camera in world coordinates (meters).
                Defaults to (0, 0).
            zoom (float, optional): The dynamic, interactive zoom level. Acts as a multiplier on
                `pixels_per_meter`. A value of 1.0 is "normal" zoom. Defaults to 1.0.
            pixels_per_meter (float, optional): The base scaling factor defining how many pixels
                represent one meter. This is typically set once to establish the default view.
                Defaults to 100.0.

        Note on `zoom` vs. `pixels_per_meter`:
            While both attributes affect the final scale, they serve different conceptual purposes.
            - `pixels_per_meter` acts as a **base scaling factor**, defining the fundamental
              relationship between world units (meters) and screen units (pixels). It's
              typically set once to establish the default view.
            - `zoom` acts as a **dynamic multiplier** for interactive adjustments. A `zoom` of 1.0
              represents the normal view based on `pixels_per_meter`. This separation makes
              user-controlled zooming more intuitive and simplifies controller logic.
        """
        # The camera's position is in world coordinates (meters)
        self.position = Vec2(0.0, 0.0) if position is None else position
        self.zoom = zoom
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.pixels_per_meter = pixels_per_meter

    @classmethod
    def with_world_width(
        cls,
        screen_width: int,
        screen_height: int,
        world_width: float,
        position: Optional[Vec2] = None,
        zoom: float = 1.0,
    ) -> "Camera":
        """
        Creates a `Camera` instance by specifying the desired visible width in world units.

        This factory is useful for setting up a camera where the field of view is defined
        by a specific width in meters, rather than by `pixels_per_meter`. It calculates
        the required `pixels_per_meter` to fit the given `world_width` into the `screen_width`.

        Args:
            screen_width (int): The width of the screen in pixels.
            screen_height (int): The height of the screen in pixels.
            world_width (float): The desired width of the visible world area in meters.
            position (Optional[Vec2], optional): The initial position of the camera in world
                coordinates. Defaults to the origin (0, 0).
            zoom (float, optional): The initial dynamic zoom level. Defaults to 1.0.

        Returns:
            Camera: A new `Camera` instance configured to match the desired world view.
        """
        # Calculate the required pixels-per-meter to fit the world width
        pixels_per_meter = screen_width / world_width
        return cls(
            screen_width=screen_width,
            screen_height=screen_height,
            position=position,
            zoom=zoom,
            pixels_per_meter=pixels_per_meter,
        )

    @property
    def scale(self) -> float:
        """
        Calculates the overall scaling factor for coordinate transformations.

        This property combines the base `pixels_per_meter` with the dynamic `zoom` level
        to produce the final scale used for converting between world and screen coordinates.
        A higher scale value means objects appear larger on screen.

        Returns:
            float: The combined scaling factor (pixels per meter).
        """
        return self.pixels_per_meter * self.zoom

    def world_to_screen(self, world_pos: Vec2) -> Vec2:
        """
        Converts a point from world coordinates to screen coordinates.

        This transformation takes a position in the physics world (in meters, with the Y-axis
        pointing up) and maps it to the corresponding pixel location on the screen (with the
        Y-axis pointing down). It accounts for the camera's position, zoom, and scaling.

        Args:
            world_pos (Vec2): The position in world coordinates (meters, Y-up).

        Returns:
            Vec2: The corresponding position in screen coordinates (pixels, Y-down).
        """
        scaled_pos = (world_pos - self.position) * self.scale

        screen_center = Vec2(self.screen_width / 2, self.screen_height / 2)

        # Flip the Y-axis here
        return Vec2(screen_center.x + scaled_pos.x, screen_center.y - scaled_pos.y)

    def screen_to_world(self, screen_pos: Vec2) -> Vec2:
        """
        Converts a point from screen coordinates to world coordinates.

        This transformation takes a pixel location on the screen (with the Y-axis pointing
        down) and maps it to the corresponding position in the physics world (in meters,
        with the Y-axis pointing up). It accounts for the camera's position, zoom, and scaling.

        Args:
            screen_pos (Vec2): The position in screen coordinates (pixels, Y-down).

        Returns:
            Vec2: The corresponding position in world coordinates (meters, Y-up).
        """
        screen_center = Vec2(self.screen_width / 2, self.screen_height / 2)
        relative_pos = screen_pos - screen_center

        # Un-flip the Y-axis here
        unflipped_pos = Vec2(relative_pos.x, -relative_pos.y)

        world_offset = unflipped_pos / self.scale
        return self.position + world_offset


class AbstractView(ABC):
    """
    An abstract base class for all View/Renderer implementations.

    This class defines the interface for a view component, which is responsible for
    all rendering tasks in the application. It decouples the simulation logic from
    the specific rendering backend (e.g., Pygame, OpenGL). Concrete implementations
    of this class must provide methods for drawing the background, physics bodies,
    UI elements, and debugging information.

    The typical rendering loop involves:
    1. Calling `render_background()` to clear the screen.
    2. Calling `render_bodies()` to draw the simulation objects.
    3. Optionally calling `render_profiler()`, `render_info()`, and the methods of
       the debug drawer to display additional information.
    4. Calling `update_display()` to present the final rendered frame.
    """

    def __init__(self, screen: Any):
        """
        Initializes a nee view instance.

        Args:
            screen (Any): The canvas on which everything is drawn.
        """
        self.screen = screen

    @abstractmethod
    def render_background(self) -> None:
        """
        Clears the screen and draws the background for a new frame.

        This method should be called at the beginning of each rendering cycle to
        prepare the display for drawing. It typically fills the screen with a solid
        color or a background image.
        """
        pass

    @abstractmethod
    def render_bodies(self, bodies: List[Body]) -> None:
        """
        Renders a list of physics bodies to the screen.

        Each body is drawn based on its shape (e.g., Polygon, Circle) and properties.
        Implementations should handle the visual representation of different body types
        and can use user-provided data for styling (e.g., color, fill).

        Args:
            bodies (List[Body]): A list of `Body` objects to be rendered.
        """
        pass

    @abstractmethod
    def update_display(self) -> None:
        """
        Updates the screen to show the final rendered frame.

        This method should be called at the end of each rendering cycle, after all
        drawing operations for the frame are complete. It handles the buffer swap
        or screen update necessary to make the rendered image visible.
        """
        pass


class PygameView(AbstractView):
    """
    A concrete implementation of the `AbstractView` using the Pygame library.

    This class handles all rendering tasks, including drawing the background,
    physics bodies, and UI elements like text and profiler information. It uses a
    `Camera` to manage the viewport and translate world coordinates to screen
    coordinates. The appearance of rendered objects can be customized through various
    settings passed during initialization.
    """

    def __init__(
        self,
        camera: Camera,
        background_color: Tuple[int, int, int] = (240, 240, 240),
        body_style_defaults: Optional[Dict[str, Any]] = None,
        window_caption: str = "Modular Physics Engine",
    ):
        """
        Initializes the PygameView.

        Args:
            camera (Camera): The camera instance that defines the viewport and
                coordinate transformations.
            background_color (Tuple[int, int, int], optional): The RGB color for the
                screen background. Defaults to (240, 240, 240).
            body_style_defaults (Optional[Dict[str, Any]], optional): Default styling
                for rendered physics bodies. Can be overridden by `user_data` on
                individual bodies. The following is the default configuration showing all
                valid keys:
                    - color: The fill color of the body (default: (50, 50, 200))
                    - outline_color: The color of the body outline (default: (0, 0, 0))
                    - outline_width: The width of the body outline (default: 1)
                    - is_filled: Whether the body is filled (default: True)
                    - circle_orientation_line: Whether to draw the orientation line for circles (default: True)
            window_caption (str, optional): The caption for the Pygame window.
                Defaults to "Modular Physics Engine".
        """
        super().__init__(
            screen=pygame.display.set_mode((camera.screen_width, camera.screen_height))
        )
        pygame.display.set_caption(window_caption)
        self.camera = camera

        # appearance settings
        self.background_color = background_color
        self.body_style_defaults = {
            "color": (60, 170, 200),
            "outline_color": (0, 0, 0),
            "outline_width": 1,
            "is_filled": True,
            "circle_orientation_line": True,
        }
        if body_style_defaults:
            self.body_style_defaults.update(body_style_defaults)

    def _render_polygon_body(self, body: Body) -> None:
        """
        Renders a single polygon-shaped body.

        This helper method handles the drawing of a polygon, including its fill
        and outline, based on the body's properties and the view's style settings.
        Styling can be customized via the body's `user_data` dictionary.

        Args:
            body (Body): The polygon-shaped body to render.
        """
        style = self.body_style_defaults.copy()
        style.update(body.user_data)

        screen_verts = [
            self.camera.world_to_screen(v)
            for v in body.shape.get_world_space_vertices(body.position, body.angle)
        ]
        if style["is_filled"]:
            pygame.draw.polygon(
                self.screen,
                style["color"],
                [v.to_int_tuple() for v in screen_verts],
                width=0,
            )
        if style["outline_width"] > 0:
            pygame.draw.polygon(
                self.screen,
                style["outline_color"],
                [v.to_int_tuple() for v in screen_verts],
                width=style["outline_width"],
            )

    def _render_circle_body(self, body: Body) -> None:
        """
        Renders a single circle-shaped body.

        This helper method handles the drawing of a circle, including its fill,
        outline, and an optional orientation line, based on the body's properties
        and the view's style settings. Styling can be customized via the body's
        `user_data` dictionary.

        Args:
            body (Body): The circle-shaped body to render.
        """
        style = self.body_style_defaults.copy()
        style.update(body.user_data)

        screen_pos = self.camera.world_to_screen(body.position)
        screen_radius = (
            self.camera.world_to_screen(body.position + Vec2(body.shape.radius, 0)).x
            - screen_pos.x
        )
        if screen_radius <= 0:
            return

        if style["is_filled"]:
            pygame.draw.circle(
                self.screen,
                style["color"],
                screen_pos.to_int_tuple(),
                screen_radius,
            )
        if style["outline_width"] > 0:
            pygame.draw.circle(
                self.screen,
                style["outline_color"],
                screen_pos.to_int_tuple(),
                screen_radius,
                width=style["outline_width"],
            )
        if style["circle_orientation_line"]:
            # Draw orientation line
            end_pos = self.camera.world_to_screen(
                body.position + Vec2(body.shape.radius, 0).rotate(body.angle)
            )
            pygame.draw.line(
                self.screen,
                style["outline_color"],
                screen_pos.to_int_tuple(),
                end_pos.to_int_tuple(),
                width=style["outline_width"],
            )

    def render_background(self) -> None:
        """
        Clears the screen and fills it with the configured background color.

        This method is an implementation of the corresponding abstract method in
        `AbstractView`. It should be called at the start of each frame's rendering
        cycle to ensure a clean canvas.
        """
        self.screen.fill(self.background_color)

    def render_bodies(self, bodies: List[Body]) -> None:
        """
        Renders a list of physics bodies to the screen.

        This method iterates through a list of `Body` objects and calls the
        appropriate private rendering method (`_render_polygon` or `_render_circle`)
        based on the body's shape type.

        The appearance of each body can be customized via its `user_data` dictionary.
        The following keys are recognized:
        - `color`: The fill color of the body.
        - `outline_color`: The color of the body's outline.
        - `outline_width`: The width of the outline in pixels.
        - `is_filled`: A boolean indicating whether to fill the shape.
        - `circle_orientation_line`: For circles, a boolean to draw a line
          indicating orientation.

        If a style key is not present in `user_data`, the default value from
        `body_style_defaults` is used.

        Args:
            bodies (List[Body]): The list of `Body` objects to render.

        Raises:
            ValueError: If a body with an unsupported shape type is encountered.
        """
        for body in bodies:
            if isinstance(body.shape, PolygonShape):
                self._render_polygon_body(body)

            elif isinstance(body.shape, CircleShape):
                self._render_circle_body(body)
            else:
                raise ValueError(f"Unsupported shape type: {type(body.shape).__name__}")

    def update_display(self) -> None:
        """
        Updates the full display surface to the screen.

        This method should be called once per frame, after all rendering is
        complete. It takes the contents of the current drawing surface and makes
        them visible to the user.
        """
        pygame.display.flip()
