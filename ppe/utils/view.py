from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Tuple

import pygame

from ppe.engine.common import Body, PolygonShape, CircleShape, Vec2
from ppe.engine.debug import AbstractDebugDrawer
from ppe.utils.profiler import Profiler

TAB10_COLORS = [
    (31, 119, 180),  # blue
    (255, 127, 14),  # orange
    (44, 160, 44),  # green
    (214, 39, 40),  # red
    (148, 103, 189),  # purple
    (140, 86, 75),  # brown
    (227, 119, 194),  # pink
    (127, 127, 127),  # gray
    (188, 189, 34),  # olive
    (23, 190, 207),  # cyan
]


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
    def render_profiler(self, profiler: Profiler) -> None:
        """
        Renders profiler information with enhanced formatting.

        Args:
            profiler: Profiler instance with timing data
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
        marker_line_length: int = 20,
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

    def _render_all_impl(self):
        """Executes all buffered draw commands for the frame."""
        # TODO use subfunctions
        if self.world_coordinate_frame_size is not None:
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

        for cmd_type, data in self._commands:
            if cmd_type == "line":
                start, end, color, arrow = data
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
                    arrow_length_screen = min(
                        (screen_end - screen_start).length() / 10, 10
                    )
                    arrow_width_screen = arrow_length_screen / 2
                    triangle_points_screem = [
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
                        [p.to_int_tuple() for p in triangle_points_screem],
                        width=0,  # filled triangle
                    )

            elif cmd_type == "circle":
                center, radius, color, filled = data
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

            elif cmd_type == "polygon":
                verts, color, filled = data
                screen_verts = [
                    self.camera.world_to_screen(v).to_int_tuple() for v in verts
                ]
                pygame.draw.polygon(
                    self.surface,
                    color,
                    screen_verts,
                    width=0 if filled else self.line_width,
                )

            elif cmd_type == "marker":
                pos, color = data
                screen_pos = self.camera.world_to_screen(pos)
                pygame.draw.circle(
                    self.surface,
                    color,
                    screen_pos.to_int_tuple(),
                    self.marker_size,
                    width=0,
                )

            elif cmd_type == "marker_line":
                start, direction, color, arrow = data
                screen_start = self.camera.world_to_screen(start)
                screen_stop = screen_start + direction * self.marker_line_length

                pygame.draw.line(
                    self.surface,
                    color,
                    screen_start.to_int_tuple(),
                    screen_stop.to_int_tuple(),
                    width=self.line_width,
                )

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
        self.profiler_font = pygame.font.SysFont("Arial", 12)
        self.profiler_colors = TAB10_COLORS
        self.profiler_bar_position = (profiler_position[0], profiler_position[1] + 25)
        self.profiler_bar_height = 20
        self.profiler_label_position = (
            self.profiler_bar_position[0],
            self.profiler_bar_position[1] + self.profiler_bar_height + 5,
        )

    def render_background(self) -> None:
        self.screen.fill(self.background_color)

    def render_bodies(self, bodies: List[Body]) -> None:
        # TODO use subfunctions for rendering different shapes
        for body in bodies:
            color = body.user_data.get("color", self.default_body_color)
            outline_color = body.user_data.get(
                "outline_color", self.default_outline_color
            )
            outline_width = body.user_data.get(
                "outline_width", self.default_outline_width
            )

            if isinstance(body.shape, PolygonShape):
                screen_verts = [
                    self.camera.world_to_screen(v)
                    for v in body.shape.get_world_space_vertices(
                        body.position, body.angle
                    )
                ]
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

            elif isinstance(body.shape, CircleShape):
                screen_pos = self.camera.world_to_screen(body.position)
                screen_radius = (
                    self.camera.world_to_screen(
                        body.position + Vec2(body.shape.radius, 0)
                    ).x
                    - screen_pos.x
                )
                if screen_radius > 0:
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

            else:
                raise ValueError(f"Unsupported shape type: {type(body.shape).__name__}")

    def render_text(
        self, text: str, position: Tuple[int, int], color: Tuple[int, int, int]
    ) -> None:
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def create_debug_drawer(self) -> AbstractDebugDrawer:
        return self._debug_drawer

    def render_profiler(self, profiler: Profiler) -> None:
        """
        Enhanced profiler visualization with a horizontal timeline bar.
        Shows timing data as segments where 1ms = pixels_per_ms in width.

        Args:
            profiler: Profiler instance with timing data
        """
        # TODO better subsection rendering
        # Get timing data in milliseconds
        if self.smooth_profiler:
            frame_time = profiler.smoothed_total_frame_time
            timings = profiler.smoothed_timings
        else:
            frame_time = profiler.total_frame_time
            timings = profiler.timings
        fps = 1000 / frame_time

        # first we have a color-coded display of the frame time
        header_text = f"{int(frame_time):03d}ms / {int(fps):02d} FPS"
        if fps > 50:
            header_color = (0, 200, 0)
        elif fps > 30:
            header_color = (255, 165, 0)
        else:
            header_color = (255, 50, 50)
        self.render_text(header_text, self.profiler_position, header_color)

        # Draw timeline background (total frame time)
        pygame.draw.rect(
            self.screen,
            (180, 180, 180),
            (
                self.profiler_bar_position[0],
                self.profiler_bar_position[1],
                int(frame_time * self.profiler_pixels_per_ms),
                self.profiler_bar_height,
            ),
            width=0,
        )

        # Draw the timing segments as colored bars
        x_offset = 0
        for i, (name, time) in enumerate(timings.items()):
            if time <= 0:
                continue

            pygame.draw.rect(
                self.screen,
                self.profiler_colors[i % len(self.profiler_colors)],
                (
                    self.profiler_bar_position[0] + x_offset,
                    self.profiler_bar_position[1],
                    int(time * self.profiler_pixels_per_ms),
                    self.profiler_bar_height,
                ),
                width=0,
            )
            x_offset += int(time * self.profiler_pixels_per_ms)

        # draw timing labels: place them sequentially next to each other below the bar
        x_offset = 0
        for i, (name, time) in enumerate(timings.items()):
            if time <= 0:
                continue

            label_color = self.profiler_colors[i % len(self.profiler_colors)]
            label_text = f"{name}: {time:.1f}ms"
            label_surface = self.profiler_font.render(label_text, True, label_color)

            # Place this label next to the previous one
            self.screen.blit(
                label_surface,
                (
                    self.profiler_label_position[0] + x_offset,
                    self.profiler_label_position[1],
                ),
            )

            # Move to the right for the next label (add some spacing)
            x_offset += label_surface.get_width() + 5

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
