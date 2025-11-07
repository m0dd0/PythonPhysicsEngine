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
from typing import List, Optional, Tuple, Dict, Any

import pygame

from ppe.engine.common import Body, PolygonShape, CircleShape, Vec2
from ppe.utils.profiler import Profiler
from ppe.frontend.colors import TAB10_COLORS
from ppe.engine.debug import DebugRecorder


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

    @abstractmethod
    def render_profiler(self, profiler: Profiler) -> None:
        """
        Renders performance profiling information to the screen.

        This method visualizes timing data from a `Profiler` instance, which can
        help in debugging performance issues. It may display information like
        frame time, FPS, and the duration of different simulation stages.

        Args:
            profiler (Profiler): The `Profiler` instance containing the timing data
                for the current frame.
        """
        pass

    @abstractmethod
    def render_info(self, info: List[str]) -> None:
        """
        Renders a list of informational strings to the screen.

        This is a general-purpose method for displaying debug information, simulation
        state, or other textual data as an overlay on the screen. Each string in
        the list is typically rendered on a new line.

        Args:
            info (List[str]): A list of strings to be rendered on the screen.
        """
        pass

    @abstractmethod
    def render_debug_recorder(self, debug_recorder: DebugRecorder) -> None:
        pass

    def render_all(
        self, bodies: List[Body], profiler: Profiler = None, info: List[str] = None
    ) -> None:
        """
        A convenience method to render the entire frame, including background,
        bodies, profiler, and info section.

        This method encapsulates the full rendering process for a single frame.
        It calls the necessary sub-methods in the correct order to produce a
        complete visual output. This is useful for simplifying the main loop
        when all components need to be rendered together.

        Args:
            bodies (List[Body]): A list of `Body` objects to be rendered.
            profiler (Profiler, optional): The `Profiler` instance for rendering
                performance data. If None, the profiler is not rendered. Defaults to None.
            info (List[str], optional): A list of informational strings to render.
                If None, no info section is rendered. Defaults to None.
        """
        self.render_background()
        self.render_bodies(bodies)
        if profiler:
            self.render_profiler(profiler)
        if info:
            self.render_info(info)
        self.update_display()


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
        profiler_settings: Optional[Dict[str, Any]] = None,
        info_section_settings: Optional[Dict[str, Any]] = None,
        debug_graphics_settings: Optional[Dict[str, Any]] = None,
        window_caption: str = "Modular Physics Engine",
        text_render_settings: Optional[Dict[str, Any]] = None,
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
            profiler_settings (Optional[Dict[str, Any]], optional): Configuration for
                the profiler display, such as position and colors. The following is the default configuration showing all
                valid keys:
                    - position: The position of the top-left of the profiler visualization (default: (10, 10))
                    - font_style: The font style for the profiler text (default: "Arial")
                    - fontsize: The font size for the profiler text (default: 12)
                    - pixels_per_ms: The scaling factor for the profiler bars (default: 8)
                    - smooth: Whether to use smoothed fps values of the profiler (default: True)
                    - colors: The color palette for the profiler bars (default: TAB10_COLORS)
                    - bar_height: The height of the profiler bars (default: 10)
            info_section_settings (Optional[Dict[str, Any]], optional): Configuration on how
                the info section gets rendered. The following is the default configuration showing all
                valid keys:
                    - position: The position of the info section (default: (10, -100))
                    - font_style: The font style for the info text (default: "Arial")
                    - fontsize: The font size for the info text (default: 12)
                    - text_color: The color of the info text (default: (0, 0, 0))
                    - line_height: The line height for the info text (default: 15)
            debug_graphics_settings (Optional[Dict[str, Any]], optional): Configuration on how
                the debug graphics get rendered. The following is the default configuration showing all
                valid keys:
                    - marker_size: The size of the markers in pixels. Defaults to 4.
                    - line_width: The width of lines and outlines in pixels. Defaults to 1.
                    - marker_line_length: The length of marker lines in pixels. Defaults to 40.
                    - world_coordinate_frame_size: The size of the world coordinate frame
                        in world units. If None, the frame is not drawn. Defaults to 1.0.
            window_caption (str, optional): The caption for the Pygame window.
                Defaults to "Modular Physics Engine".
            text_render_settings (Optional[Dict[str, Any]], optional): Default
                settings for rendering text, such as font style and size. Note that the text
                in the profiler and info section uses their own font setting. This setting
                is merely responsible for explicit calls to the render_text_* methods of
                the view. Default is:
                    - font_style: "Arial"
                    - fontsize: 12
        """
        self.camera = camera
        self.screen = pygame.display.set_mode(
            (camera.screen_width, camera.screen_height)
        )
        pygame.display.set_caption(window_caption)

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

        # info rendering settings
        self.info_section_settings = {
            "position": (10, -100),
            "fontsize": 12,
            "font_style": "Arial",
            "text_color": (0, 0, 0),
            "line_height": 15,
        }
        if info_section_settings:
            self.info_section_settings.update(info_section_settings)
        self.info_section_settings["font"] = pygame.font.SysFont(
            self.info_section_settings["font_style"],
            self.info_section_settings["fontsize"],
        )

        # profiler settings
        self.profiler_settings = {
            "position": (10, 10),
            "font_style": "Arial",
            "fontsize": 12,
            "pixels_per_ms": 8,
            "smooth": True,
            "colors": TAB10_COLORS,
            "bar_background_color": (200, 200, 200),
            "subsection_keys": [],
            "label_font_style": "Arial",
            "label_font_size": 12,
            "row_height": 15,
            "row_spacing": 2,
            "horizontal_bar_offset": 70,
        }
        if profiler_settings:
            self.profiler_settings.update(profiler_settings)
        self.profiler_settings["font"] = pygame.font.SysFont(
            self.profiler_settings["font_style"],
            self.profiler_settings["fontsize"],
        )
        self.profiler_settings["label_font"] = pygame.font.SysFont(
            self.profiler_settings["label_font_style"],
            self.profiler_settings["label_font_size"],
        )

        # text rendering settings
        self.text_render_settings = {
            "font_style": "Arial",
            "fontsize": 12,
        }
        if text_render_settings:
            self.text_render_settings.update(text_render_settings)
        self.text_render_settings["font"] = pygame.font.SysFont(
            self.text_render_settings["font_style"],
            self.text_render_settings["fontsize"],
        )

        # debug graphics settings
        self.debug_graphics_settings = {
            "marker_size": 4,
            "line_width": 1,
            "marker_line_length": 40,
            "world_coordinate_frame_size": 1.0,
        }
        if debug_graphics_settings is not None:
            self.debug_graphics_settings.update(debug_graphics_settings)

    def _resolve_position(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Resolves the given position to be within the screen bounds."""
        x, y = position
        if x < 0:
            x = self.camera.screen_width + position[0]
        if y < 0:
            y = self.camera.screen_height + position[1]
        return (x, y)

    def _render_line_screen(
        self,
        start: Vec2,
        end: Vec2,
        color: Tuple[int, int, int],
        line_width: int,
        arrow: bool = False,
    ):
        """
        Renders a line segment from a start to an end point. All values are in pixel coordinates.
        An optional arrowhead can be drawn at the end point.

        Args:
            start (Vec2): The starting point of the line in screen coordinates.
            end (Vec2): The ending point of the line in screen coordinates.
            color (Tuple[int, int, int]): The RGB color of the line.
            arrow (bool, optional): If True, an arrowhead is drawn at the end.
                Defaults to False.
            line_width (int, optional): The width of the line.
        """
        pygame.draw.line(
            self.screen,
            color,
            start.to_int_tuple(),
            end.to_int_tuple(),
            width=line_width,
        )

        if arrow:
            direction = (end - start).normalize()
            arrow_length_screen = 8
            arrow_width_screen = 6

            triangle_points_screen = [
                end,
                end
                - direction * arrow_length_screen
                + Vec2(-direction.y, direction.x) * 0.5 * arrow_width_screen,
                end
                - direction * arrow_length_screen
                + Vec2(direction.y, -direction.x) * 0.5 * arrow_width_screen,
            ]

            pygame.draw.polygon(
                self.screen,
                color,
                [p.to_int_tuple() for p in triangle_points_screen],
                width=0,  # filled triangle
            )

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

    def _render_profiler_bar(
        self,
        position: Tuple[int, int],
        timings: Dict[str, float],
        heading: str,
    ) -> None:
        """Renders a horizontal bar for the profiler including its heading and the labels.

        Args:
            position (Tuple[int, int]): The (x, y) position to render the bar.
            timings (Dict[str, float]): A dictionary of timing data for each section.
            heading (str): The heading text to display above the bar.
            total_timing (float): The total timing value for the bar. This will draw a background
                rectangle for the bar. Ignored if set to None.
        """
        # draw the header text
        self.screen.blit(
            self.profiler_settings["font"].render(heading, True, (0, 0, 0)),
            (position[0], position[1]),
        )

        bar_position = (
            position[0] + self.profiler_settings["horizontal_bar_offset"],
            position[1],
        )

        # compute the section based properties
        section_widths = [
            int(timing * self.profiler_settings["pixels_per_ms"])
            for timing in timings.values()
        ]
        section_colors = [
            self.profiler_settings["colors"][i % len(self.profiler_settings["colors"])]
            for i in range(len(timings))
        ]
        total_time = sum(timings.values())
        section_labels = [
            f"{key} ({int(value):02d}ms/{int(value / total_time * 100):02d}%)"
            for key, value in timings.items()
        ]

        # draw the colored sections
        section_x_position = bar_position[0]
        for width, color, label in zip(section_widths, section_colors, section_labels):
            pygame.draw.rect(
                self.screen,
                color,
                (
                    section_x_position,
                    bar_position[1],
                    width,
                    self.profiler_settings["row_height"],
                ),
                width=0,
            )

            # draw the label with correct width
            for i in range(len(label)):
                if self.profiler_settings["label_font"].size(label[:i])[0] > width:
                    label = label[: i - 1]
                    break
            label_rect = self.profiler_settings["label_font"].render(
                label, True, (0, 0, 0)
            )
            self.screen.blit(
                label_rect,
                (
                    section_x_position + (width - label_rect.get_width()) // 2,
                    bar_position[1],
                ),
            )

            section_x_position += width

    def _render_coordinate_frame(
        self,
        coordinate_frame_size: float,
        position: Vec2,
        line_width: int,
        rotation: float = 0.0,
    ):
        """
        Renders a coordinate frame at the world origin.

        The X-axis is drawn in red, and the Y-axis is drawn in green.
        This provides a visual reference for the world's coordinate system.

        Args:
            coordinate_frame_size (float): The length of the coordinate frame's axes in world units.
            position (Vec2): The position of the coordinate frame in world coordinates.
            line_width (int): The width of the coordinate frame's lines in pixels.
            rotation (float): The rotation of the coordinate frame in radians.
        """
        self._render_line_screen(
            start=self.camera.world_to_screen(position),
            end=self.camera.world_to_screen(
                position + Vec2(coordinate_frame_size, 0).rotate(rotation)
            ),
            color=(255, 0, 0),
            arrow=True,
            line_width=line_width,
        )
        self._render_line_screen(
            start=self.camera.world_to_screen(position),
            end=self.camera.world_to_screen(
                position + Vec2(0, coordinate_frame_size).rotate(rotation)
            ),
            color=(0, 255, 0),
            arrow=True,
            line_width=line_width,
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

    def render_profiler(self, profiler: Profiler) -> None:
        """
        Renders an enhanced profiler visualization with a horizontal timeline bar.

        This method displays timing data from the `Profiler` as a series of
        color-coded segments, where the width of each segment is proportional to
        the time taken. It shows total frame time, FPS, and detailed breakdowns
        for top-level and specified subsection timings. Timing entries that do not contain
        a `/` will be treated as top-level entries and displayed in a shared bar.
        Entries with a `/` will be grouped by the preceding section name and displayed
        in separate bars per leading section. Note that only one level of nesting is supported.

        Args:
            profiler (Profiler): The `Profiler` instance with the timing data to render.
        """
        # Get timing data in milliseconds
        if self.profiler_settings["smooth"]:
            frame_time = profiler.smoothed_total_frame_time
            timings = profiler.smoothed_timings
        else:
            frame_time = profiler.total_frame_time
            timings = profiler.timings

        # resolve position
        position = self._resolve_position(self.profiler_settings["position"])

        # render the color bar for the top-level timings
        toplevel_timings = {k: v for k, v in timings.items() if "/" not in k}
        self._render_profiler_bar(
            position=position,
            timings=toplevel_timings,
            # heading=f"{int(frame_time):03d}ms ({int(1000 / frame_time):02d} FPS)",
            heading=f"total ({int(frame_time):03d}ms)",
        )

        # render subsection bars below the main bar
        y_position = position[1]
        for subsection_key in self.profiler_settings["subsection_keys"]:
            y_position += (
                self.profiler_settings["row_height"]
                + self.profiler_settings["row_spacing"]
            )
            subsections_timings = {
                k.split("/")[1]: v
                for k, v in timings.items()
                if k.startswith(f"{subsection_key}/")
            }
            if not subsections_timings:
                continue

            self._render_profiler_bar(
                position=[position[0], y_position],
                timings=subsections_timings,
                heading=f"{subsection_key} ({int(sum(subsections_timings.values())):03d}ms)",
            )

    def render_info(self, info: List[str]) -> None:
        """
        Renders a list of informational strings to the screen.

        This method displays each string in the provided list as a separate line
        of text in a designated area of the screen, configured by
        `info_section_settings`. It's useful for showing debug data, controls,
        or simulation status.

        Args:
            info (List[str]): A list of strings to render as information.
        """
        ## resolve position
        position = self._resolve_position(self.info_section_settings["position"])

        for i, line in enumerate(info):
            text_surface = self.info_section_settings["font"].render(
                line, True, self.info_section_settings["text_color"]
            )
            self.screen.blit(
                text_surface,
                (
                    position[0],
                    position[1] + i * self.info_section_settings["line_height"],
                ),
            )

    def render_debug_recorder(self, debug_recorder: DebugRecorder):
        """
        Triggers the rendering of all scheduled debug graphics.

        This method iterates through the queue of drawing commands scheduled via
        the `add_*` methods and renders them to the Pygame surface. The queue is
        cleared after rendering. This should be called once per frame.
        """
        if (
            self.debug_graphics_settings["world_coordinate_frame_size"] is not None
            and debug_recorder.enabled
        ):
            self._render_coordinate_frame(
                position=Vec2(0, 0),
                coordinate_frame_size=self.debug_graphics_settings[
                    "world_coordinate_frame_size"
                ],
                line_width=1,
            )

        for cmd_type, data in debug_recorder.command_queue:
            if cmd_type == "line":
                start, end, color, arrow = data
                self._render_line_screen(
                    self.camera.world_to_screen(start),
                    self.camera.world_to_screen(end),
                    color,
                    line_width=self.debug_graphics_settings["line_width"],
                    arrow=arrow,
                )

            elif cmd_type == "circle":
                center, radius, color, filled = data
                pygame.draw.circle(
                    self.screen,
                    color,
                    self.camera.world_to_screen(center).to_int_tuple(),
                    int(radius * self.camera.scale),
                    width=0 if filled else self.debug_graphics_settings["line_width"],
                )

            elif cmd_type == "polygon":
                verts, color, filled = data
                pygame.draw.polygon(
                    self.screen,
                    color,
                    [self.camera.world_to_screen(v).to_int_tuple() for v in verts],
                    width=0 if filled else self.debug_graphics_settings["line_width"],
                )

            elif cmd_type == "marker":
                position, color = data
                pygame.draw.circle(
                    self.screen,
                    color,
                    self.camera.world_to_screen(position).to_int_tuple(),
                    int(self.debug_graphics_settings["marker_size"]),
                    width=0,
                )

            elif cmd_type == "marker_line":
                start, direction, color, arrow = data
                start_screen = self.camera.world_to_screen(start)
                end_screen = self.camera.world_to_screen(start + direction)
                end_screen = (
                    start_screen
                    + (end_screen - start_screen).normalize()
                    * self.debug_graphics_settings["marker_line_length"]
                )
                self._render_line_screen(
                    start_screen,
                    end_screen,
                    color,
                    line_width=self.debug_graphics_settings["line_width"],
                    arrow=arrow,
                )

        debug_recorder.command_queue.clear()

    def update_display(self) -> None:
        """
        Updates the full display surface to the screen.

        This method should be called once per frame, after all rendering is
        complete. It takes the contents of the current drawing surface and makes
        them visible to the user.
        """
        pygame.display.flip()
