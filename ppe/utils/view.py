from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import pygame

from ppe.engine.common import Body, PolygonShape, CircleShape, Vec2
from ppe.engine.debug import AbstractDebugDrawer
from ppe.utils.profiler import Profiler
from ppe.utils.colors import TAB10_COLORS


class Camera:
    def __init__(
        self,
        screen_width: int,  # in pixels
        screen_height: int,  # in pixels
        position: Optional[Vec2] = None,
        zoom: float = 1.0,
        pixels_per_meter: float = 100.0,
    ):
        """
        Initializes the Camera.

        Args:
            screen_width: The width of the screen in pixels.
            screen_height: The height of the screen in pixels.
            zoom: The initial zoom level. 1.0 is normal zoom.
            pixels_per_meter: The number of pixels that represent one meter.
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
        A factory to create a Camera by defining the desired visible width
        in world units (meters).

        Args:
            screen_width: The width of the screen in pixels.
            screen_height: The height of the screen in pixels.
            world_width: The desired width of the view in meters.
            zoom: The initial zoom level.

        Returns:
            A new Camera instance configured to the desired view.
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
        """The combined scale factor of pixels-per-meter and zoom."""
        return self.pixels_per_meter * self.zoom

    def world_to_screen(self, world_pos: Vec2) -> Vec2:
        """Converts world coordinates (meters, Y-up) to screen (pixel, Y-down) coordinates."""
        scaled_pos = (world_pos - self.position) * self.scale

        screen_center = Vec2(self.screen_width / 2, self.screen_height / 2)

        # Flip the Y-axis here
        return Vec2(screen_center.x + scaled_pos.x, screen_center.y - scaled_pos.y)

    def screen_to_world(self, screen_pos: Vec2) -> Vec2:
        """Converts screen coordinates (pixels, Y-down) to world coordinates (meters, Y-up)."""
        screen_center = Vec2(self.screen_width / 2, self.screen_height / 2)
        relative_pos = screen_pos - screen_center

        # Un-flip the Y-axis here
        unflipped_pos = Vec2(relative_pos.x, -relative_pos.y)

        world_offset = unflipped_pos / self.scale
        return self.position + world_offset


class AbstractView(ABC):
    """An abstract base class for all View/Renderer implementations."""

    @abstractmethod
    def render_background(self) -> None:
        """Clears the screen and draws the background."""
        pass

    @abstractmethod
    def render_bodies(self, bodies: List[Body]) -> None:
        """Renders the primary physics bodies."""
        pass

    @abstractmethod
    def render_text(
        self, text: str, position: Tuple[int, int], color: Tuple[int, int, int]
    ) -> None:
        """Renders UI text to the screen."""
        pass

    @abstractmethod
    def create_debug_drawer(self) -> AbstractDebugDrawer:
        """Creates a debug drawer instance compatible with this view."""
        pass

    @abstractmethod
    def update_display(self) -> None:
        """Updates the screen to show the final rendered frame."""
        pass

    @abstractmethod
    def render_profiler(
        self, profiler: Profiler, subsections: List[str] = None
    ) -> None:
        """
        Renders profiler information with enhanced formatting.

        Args:
            profiler: Profiler instance with timing data
            subsections: Optional list of subsection names to display.
        """
        pass

    @abstractmethod
    def render_info(self, info: List[str]) -> None:
        """
        Renders additional information to the screen, such as debug info or
        simulation state.

        Args:
            info: A list of strings to render as information.
        """
        pass


class PygameDebugDrawer(AbstractDebugDrawer):
    """A concrete implementation of the debug drawer for Pygame."""

    def __init__(
        self,
        surface: pygame.Surface,
        camera: Camera,
        marker_size: int = 4,
        line_width: int = 1,
        marker_line_length: int = 40,
        world_coordinate_frame_size: Optional[float] = 1.0,
    ):
        super().__init__()  # Initialize the enabled flag
        self.surface = surface
        self.camera = camera
        self.marker_size = marker_size
        self.line_width = line_width
        self.marker_line_length = marker_line_length
        self.world_coordinate_frame_size = world_coordinate_frame_size

        self._commands = []

    def _add_line_impl(self, start: Vec2, end: Vec2, color=(0, 0, 0), arrow=False):
        self._commands.append(("line", (start, end, color, arrow)))

    def _add_circle_impl(
        self, center: Vec2, radius: float, color=(0, 0, 0), filled=False
    ):
        self._commands.append(("circle", (center, radius, color, filled)))

    def _add_polygon_impl(self, vertices: List[Vec2], color=(0, 0, 0), filled=False):
        self._commands.append(("polygon", (vertices, color, filled)))

    def _add_marker_impl(self, position: Vec2, color=(255, 0, 0)):
        self._commands.append(("marker", (position, color)))

    def _add_marker_line_impl(
        self, start: Vec2, direction: Vec2, color=(255, 0, 0), arrow=False
    ):
        self._commands.append(("marker_line", (start, direction, color, arrow)))

    def _add_text_world_impl(
        self, position: Vec2, text: str, color=(0, 0, 0), size: float = 12.0
    ):
        self._commands.append(("text_world", (position, text, color, size)))

    def _add_text_screen_impl(
        self, position: Vec2, text: str, color=(0, 0, 0), size: float = 12.0
    ):
        self._commands.append(("text_screen", (position, text, color, size)))

    def _render_coordinate_frame(self):
        """Renders a coordinate frame at the origin."""
        self._add_line_impl(
            Vec2(0, 0),
            Vec2(self.world_coordinate_frame_size, 0),
            color=(255, 0, 0),
            arrow=True,
        )
        self._add_line_impl(
            Vec2(0, 0),
            Vec2(0, self.world_coordinate_frame_size),
            color=(0, 255, 0),
            arrow=True,
        )

    def _render_line(
        self, start: Vec2, end: Vec2, color: Tuple[int, int, int], arrow: bool = False
    ):
        """Renders a line from start to end with an optional arrow."""
        screen_start = self.camera.world_to_screen(start)
        screen_end = self.camera.world_to_screen(end)
        pygame.draw.line(
            self.surface,
            color,
            screen_start.to_int_tuple(),
            screen_end.to_int_tuple(),
            width=self.line_width,
        )

        if arrow:
            direction = (screen_end - screen_start).normalize()
            arrow_length_screen = min((screen_end - screen_start).length() / 5, 50)
            arrow_width_screen = arrow_length_screen / 2
            triangle_points_screen = [
                screen_end,
                screen_end
                - direction * arrow_length_screen
                + Vec2(-direction.y, direction.x) * 0.5 * arrow_width_screen,
                screen_end
                - direction * arrow_length_screen
                + Vec2(direction.y, -direction.x) * 0.5 * arrow_width_screen,
            ]
            pygame.draw.polygon(
                self.surface,
                color,
                [p.to_int_tuple() for p in triangle_points_screen],
                width=0,  # filled triangle
            )

    def _render_circle(
        self, center: Vec2, radius: float, color: Tuple[int, int, int], filled: bool
    ):
        """Renders a circle at the specified center with a given radius."""
        screen_center = self.camera.world_to_screen(center)
        screen_radius = int(radius * self.camera.zoom)
        if screen_radius > 0:
            pygame.draw.circle(
                self.surface,
                color,
                screen_center.to_int_tuple(),
                screen_radius,
                width=0 if filled else self.line_width,
            )

    def _render_polygon(
        self, vertices: List[Vec2], color: Tuple[int, int, int], filled: bool
    ):
        """Renders a polygon defined by the given vertices."""
        screen_verts = [self.camera.world_to_screen(v).to_int_tuple() for v in vertices]
        pygame.draw.polygon(
            self.surface,
            color,
            screen_verts,
            width=0 if filled else self.line_width,
        )

    def _render_marker(self, position: Vec2, color: Tuple[int, int, int]):
        """Renders a marker at the specified position."""
        screen_pos = self.camera.world_to_screen(position)
        pygame.draw.circle(
            self.surface,
            color,
            screen_pos.to_int_tuple(),
            self.marker_size,
            width=0,  # filled circle
        )

    def _render_marker_line(
        self,
        start: Vec2,
        direction: Vec2,
        color: Tuple[int, int, int],
        arrow: bool = False,
    ):
        """Renders a line with an optional arrow starting from a point in a given direction."""
        # in order to use the _render_line method, we need to calculate the end point in
        # world coordinates
        screen_start = self.camera.world_to_screen(start)
        screen_end = self.camera.world_to_screen(start + direction)
        screen_direction = screen_end - screen_start
        screen_end = screen_start + (screen_direction.normalize() * self.marker_line_length)
        world_end = self.camera.screen_to_world(screen_end)
        self._render_line(start, world_end, color, arrow)

    def _render_text_world(
        self, position: Vec2, text: str, color: Tuple[int, int, int], size: float
    ):
        """Renders text at a world position."""
        # Create a font for the specific size
        font = pygame.font.SysFont("Arial", int(size))
        text_surface = font.render(text, True, color)
        
        # Convert world position to screen coordinates
        screen_pos = self.camera.world_to_screen(position)
        self.surface.blit(text_surface, screen_pos.to_int_tuple())

    def _render_text_screen(
        self, position: Vec2, text: str, color: Tuple[int, int, int], size: float
    ):
        """Renders text at a screen position."""
        # Create a font for the specific size
        font = pygame.font.SysFont("Arial", int(size))
        text_surface = font.render(text, True, color)
        
        # Use screen position directly
        self.surface.blit(text_surface, position.to_int_tuple())

    def _render_all_impl(self):
        """Executes all buffered draw commands for the frame."""
        if self.world_coordinate_frame_size is not None:
            self._render_coordinate_frame()

        for cmd_type, data in self._commands:
            if cmd_type == "line":
                start, end, color, arrow = data
                self._render_line(start, end, color, arrow)

            elif cmd_type == "circle":
                center, radius, color, filled = data
                self._render_circle(center, radius, color, filled)

            elif cmd_type == "polygon":
                verts, color, filled = data
                self._render_polygon(verts, color, filled)

            elif cmd_type == "marker":
                position, color = data
                self._render_marker(position, color)

            elif cmd_type == "marker_line":
                start, direction, color, arrow = data
                self._render_marker_line(start, direction, color, arrow)

            elif cmd_type == "text_world":
                position, text, color, size = data
                self._render_text_world(position, text, color, size)

            elif cmd_type == "text_screen":
                position, text, color, size = data
                self._render_text_screen(position, text, color, size)

        self._commands.clear()


class PygameView(AbstractView):
    """The View, responsible for all rendering using Pygame."""

    def __init__(
        self,
        camera: Camera,
        background_color: Tuple[int, int, int] = (240, 240, 240),
        default_body_color: Tuple[int, int, int] = (50, 50, 200),
        default_outline_color: Tuple[int, int, int] = (0, 0, 0),
        default_outline_width: int = 1,
        default_is_filled: bool = True,
        profiler_position: Tuple[int, int] = (10, 10),
        profiler_pixels_per_ms: int = 8,
        smooth_profiler: bool = True,
        info_position: Tuple[int, int] = None,
    ):
        self.camera = camera
        self.screen = pygame.display.set_mode(
            (camera.screen_width, camera.screen_height)
        )
        pygame.display.set_caption("Modular Physics Engine")
        self.font = pygame.font.SysFont("Arial", 18)

        self._debug_drawer = PygameDebugDrawer(self.screen, self.camera)

        # appearance settings
        self.background_color = background_color
        self.default_body_color = default_body_color
        self.default_outline_color = default_outline_color
        self.default_outline_width = default_outline_width
        self.default_is_filled = default_is_filled
        self.default_circle_orientation_line = True

        # info rendering settings
        self.info_position = (
            info_position if info_position else (10, camera.screen_height - 100)
        )
        self.info_font = pygame.font.SysFont("Arial", 12)
        self.info_line_height = 15  # height of each line in the info display
        self.info_color = (0, 0, 0)  # default color for info text

        # profiler settings
        self.profiler_position = profiler_position
        self.profiler_pixels_per_ms = profiler_pixels_per_ms
        self.smooth_profiler = smooth_profiler
        self.profiler_label_font = pygame.font.SysFont("Arial", 12)
        self.profiler_header_font = pygame.font.SysFont("Arial", 12)
        self.profiler_colors = TAB10_COLORS
        self.profiler_bar_position = (profiler_position[0] + 80, profiler_position[1])
        self.profiler_bar_height = 10
        self.profiler_label_position = (
            self.profiler_bar_position[0],
            self.profiler_bar_position[1] + self.profiler_bar_height + 5,
        )
        self.profiler_bar_background_color = (180, 180, 180)
        self.fps_color_profile = {
            50: (0, 200, 0),  # green for >50 FPS
            30: (255, 165, 0),  # orange for >30
            0: (255, 50, 50),  # red for <=30 FPS
        }

    def render_background(self) -> None:
        self.screen.fill(self.background_color)

    def _render_polygon(self, body: Body) -> None:
        filled = body.user_data.get("filled", self.default_is_filled)
        color = body.user_data.get("color", self.default_body_color)
        outline_color = body.user_data.get("outline_color", self.default_outline_color)
        outline_width = body.user_data.get("outline_width", self.default_outline_width)

        screen_verts = [
            self.camera.world_to_screen(v)
            for v in body.shape.get_world_space_vertices(body.position, body.angle)
        ]
        if filled:
            pygame.draw.polygon(
                self.screen,
                color,
                [v.to_int_tuple() for v in screen_verts],
                width=0,
            )
        if outline_width > 0:
            pygame.draw.polygon(
                self.screen,
                outline_color,
                [v.to_int_tuple() for v in screen_verts],
                width=outline_width,
            )

    def _render_circle(self, body: Body) -> None:
        filled = body.user_data.get("filled", self.default_is_filled)
        color = body.user_data.get("color", self.default_body_color)
        outline_color = body.user_data.get("outline_color", self.default_outline_color)
        outline_width = body.user_data.get("outline_width", self.default_outline_width)
        orientation_line = body.user_data.get(
            "orientation_line", self.default_circle_orientation_line
        )

        screen_pos = self.camera.world_to_screen(body.position)
        screen_radius = (
            self.camera.world_to_screen(body.position + Vec2(body.shape.radius, 0)).x
            - screen_pos.x
        )
        if screen_radius <= 0:
            return

        if filled:
            pygame.draw.circle(
                self.screen, color, screen_pos.to_int_tuple(), screen_radius
            )
        if outline_width > 0:
            pygame.draw.circle(
                self.screen,
                outline_color,
                screen_pos.to_int_tuple(),
                screen_radius,
                width=outline_width,
            )
        if orientation_line:
            # Draw orientation line
            end_pos = self.camera.world_to_screen(
                body.position + Vec2(body.shape.radius, 0).rotate(body.angle)
            )
            pygame.draw.line(
                self.screen,
                outline_color,
                screen_pos.to_int_tuple(),
                end_pos.to_int_tuple(),
                width=outline_width,
            )

    def render_bodies(self, bodies: List[Body]) -> None:
        for body in bodies:
            if isinstance(body.shape, PolygonShape):
                self._render_polygon(body)

            elif isinstance(body.shape, CircleShape):
                self._render_circle(body)
            else:
                raise ValueError(f"Unsupported shape type: {type(body.shape).__name__}")

    def render_text(
        self, text: str, position: Tuple[int, int], color: Tuple[int, int, int]
    ) -> None:
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def create_debug_drawer(self) -> AbstractDebugDrawer:
        return self._debug_drawer

    def _render_color_bar(
        self,
        position: Tuple[int, int],
        section_widths: List[int],
        height: int = 20,
        colors: List[Tuple[int, int, int]] = None,
        total_width: int = None,
        background_color: Tuple[int, int, int] = (240, 240, 240),
        labels: List[str] = None,
        label_font: Optional[pygame.font.Font] = None,
    ) -> None:
        # input validation
        if colors is None:
            colors = [
                TAB10_COLORS[i % len(TAB10_COLORS)] for i in range(len(section_widths))
            ]
        elif len(colors) != len(section_widths):
            raise ValueError("Colors must match the number of sections.")

        # draw background
        if total_width is not None:
            pygame.draw.rect(
                self.screen,
                background_color,
                (position[0], position[1], total_width, height),
                width=0,
            )

        # draw the colored sections
        x_offset = position[0]
        for width, color in zip(section_widths, colors):
            pygame.draw.rect(
                self.screen,
                color,
                (x_offset, position[1], width, height),
                width=0,
            )
            x_offset += width

        # draw labels if provided
        if labels is not None:
            if len(labels) != len(section_widths):
                raise ValueError("Labels must match the number of sections.")

            label_font = label_font or self.font
            x_offset = position[0]
            for label, color in zip(labels, colors):
                label_surface = label_font.render(label, True, color)
                self.screen.blit(
                    label_surface,
                    (x_offset, position[1] + height),
                )
                x_offset += label_surface.get_width() + 10

    def _get_fps_color(self, fps: float) -> Tuple[int, int, int]:
        for threshold, color in self.fps_color_profile.items():
            if fps > threshold:
                return color
        raise ValueError(
            "FPS must be a positive number or the fps_color_profile is not properly defined."
        )

    def render_profiler(
        self, profiler: Profiler, subsections: List[str] = None
    ) -> None:
        """
        Enhanced profiler visualization with a horizontal timeline bar.
        Shows timing data as segments where 1ms = pixels_per_ms in width.

        Args:
            profiler: Profiler instance with timing data
        """
        subsections = subsections or []

        # Get timing data in milliseconds
        if self.smooth_profiler:
            frame_time = profiler.smoothed_total_frame_time
            timings = profiler.smoothed_timings
        else:
            frame_time = profiler.total_frame_time
            timings = profiler.timings
        fps = 1000 / frame_time
        toplevel_timings = {k: v for k, v in timings.items() if "/" not in k}

        # first we have a color-coded display of the frame time
        text_surface = self.profiler_header_font.render(
            f"{int(frame_time):03d}ms / {int(fps):02d} FPS",
            True,
            self._get_fps_color(fps),
        )
        self.screen.blit(text_surface, self.profiler_position)

        # render the color bar for the top-level timings
        self._render_color_bar(
            position=self.profiler_bar_position,
            section_widths=[
                int(timing * self.profiler_pixels_per_ms)
                for timing in toplevel_timings.values()
            ],
            height=self.profiler_bar_height,
            colors=[
                self.profiler_colors[i % len(self.profiler_colors)]
                for i in range(len(toplevel_timings))
            ],
            total_width=int(frame_time * self.profiler_pixels_per_ms),
            background_color=self.profiler_bar_background_color,
            labels=[
                f"{key} ({int(value):02d}ms/{int(value / frame_time * 100):02d}%)"
                for key, value in toplevel_timings.items()
            ],
            label_font=self.profiler_label_font,
        )

        # render subsection bars below the main bar
        y_spacing = self.profiler_bar_height + text_surface.get_height() + 5
        for i_sub, subsection in enumerate(subsections):
            subsections_timings = {
                k: v for k, v in timings.items() if k.startswith(subsection + "/")
            }
            if not subsections_timings:
                continue

            # render the subsection header
            self.screen.blit(
                self.profiler_header_font.render(subsection, True, (0, 0, 0)),
                (
                    self.profiler_position[0],
                    self.profiler_position[1] + (i_sub + 1) * y_spacing,
                ),
            )

            # render the subsection color bar
            self._render_color_bar(
                position=(
                    self.profiler_bar_position[0],
                    self.profiler_bar_position[1] + (i_sub + 1) * y_spacing,
                ),
                section_widths=[
                    int(timing * self.profiler_pixels_per_ms)
                    for timing in subsections_timings.values()
                ],
                height=self.profiler_bar_height,
                colors=[
                    self.profiler_colors[i % len(self.profiler_colors)]
                    for i in range(len(subsections_timings))
                ],
                total_width=None,
                labels=[
                    f"{key[len(subsection)+1:]} ({int(value):02d}ms/{int(value / frame_time * 100):02d}%)"
                    for key, value in subsections_timings.items()
                ],
                label_font=self.profiler_label_font,
            )

    def render_info(self, info: List[str]) -> None:
        """
        Renders additional information to the screen, such as debug info or
        simulation state.

        Args:
            info: A list of strings to render as information.
        """
        for i, line in enumerate(info):
            text_surface = self.info_font.render(line, True, self.info_color)
            self.screen.blit(
                text_surface,
                (
                    self.info_position[0],
                    self.info_position[1] + i * self.info_line_height,
                ),
            )

    def update_display(self) -> None:
        pygame.display.flip()
