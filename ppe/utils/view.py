from abc import ABC, abstractmethod
from typing import List, Optional

import pygame

from ppe.engine.common import Body, PolygonShape, CircleShape, Vec2
from ppe.engine.debug import AbstractDebugDrawer


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
    def render_text(self, text: str, position: tuple) -> None:
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

    def render_all(self, world, info_data: dict = None) -> None:
        """
        Renders the complete frame: background, bodies, debug, and info.
        Default implementation calls individual render methods.

        Args:
            world: The world containing bodies and debug drawer
            info_data: Optional dictionary of info text to display
        """
        self.render_background()
        self.render_bodies(world.bodies)

        world.debug_drawer.render_all()

        if info_data:
            self.render_info(info_data)

    def render_info(self, info_dict: dict) -> None:
        """
        Renders informational text in a consistent format.
        Default implementation calls render_text for each item.

        Args:
            info_dict: Dictionary of label: value pairs to display
        """
        # Default implementation - subclasses should override with their specific layout
        y_offset = 0
        start_pos = (10, 10)
        line_height = 20
        for label, value in info_dict.items():
            text = f"{label}: {value}"
            self.render_text(text, (start_pos[0], start_pos[1] + y_offset))
            y_offset += line_height


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
        background_color=(240, 240, 240),
        default_body_color=(50, 50, 200),
        default_outline_color=(0, 0, 0),
        default_outline_width=1,
        info_start_pos=(10, 10),
        info_line_height=20,
    ):
        self.camera = camera
        self.screen = pygame.display.set_mode(
            (camera.screen_width, camera.screen_height)
        )
        pygame.display.set_caption("Modular Physics Engine")
        self.font = pygame.font.SysFont("Arial", 18)

        self._debug_drawer = PygameDebugDrawer(self.screen, self.camera)
        self.background_color = background_color
        self.default_body_color = default_body_color
        self.default_outline_color = default_outline_color
        self.default_outline_width = default_outline_width
        self.info_start_pos = info_start_pos
        self.info_line_height = info_line_height

    def render_background(self) -> None:
        self.screen.fill(self.background_color)

    def render_bodies(self, bodies: List[Body]) -> None:
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
                screen_radius = self.camera.world_to_screen(
                    body.position + Vec2(body.shape.radius, 0)
                ).x - screen_pos.x
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
                raise ValueError(
                    f"Unsupported shape type: {type(body.shape).__name__}"
                )

    def render_text(self, text: str, position: tuple) -> None:
        text_surface = self.font.render(text, True, (0, 0, 0))
        self.screen.blit(text_surface, position)

    def create_debug_drawer(self) -> AbstractDebugDrawer:
        return self._debug_drawer

    def render_all(self, world, info_data: dict = None) -> None:
        """
        Renders the complete frame: background, bodies, debug, and info.

        Args:
            world: The world containing bodies and debug drawer
            info_data: Optional dictionary of info text to display
        """
        self.render_background()
        self.render_bodies(world.bodies)

        world.debug_drawer.render_all()

        if info_data:
            self.render_info(info_data)

    def render_info(self, info_dict: dict) -> None:
        """
        Renders informational text in a consistent format using instance attributes.

        Args:
            info_dict: Dictionary of label: value pairs to display
        """
        y_offset = 0
        for label, value in info_dict.items():
            text = f"{label}: {value}"
            self.render_text(
                text, (self.info_start_pos[0], self.info_start_pos[1] + y_offset)
            )
            y_offset += self.info_line_height

    def update_display(self) -> None:
        pygame.display.flip()
