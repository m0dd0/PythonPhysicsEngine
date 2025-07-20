from abc import ABC, abstractmethod
from typing import Tuple

from ppe.engine.common import Vec2


class AbstractDebugDrawer(ABC):
    """An abstract base class for all debug drawer strategies."""

    def __init__(self):
        """Initialize the debug drawer with enabled state."""
        self.enabled = True

    def add_line(
        self,
        start: Vec2,
        end: Vec2,
        color: Tuple[int, int, int] = (0, 0, 0),
        arrow: bool = False,
    ) -> None:
        """
        Adds a line from start to end with the specified color to the render queue.

        Args:
            start: The starting point of the line in world space.
            end: The ending point of the line in world space.
            color: The color of the line.
            arrow: Whether to draw an arrow at the end.
        """
        if not self.enabled:
            return
        self._add_line_impl(start, end, color, arrow)

    def add_circle(
        self,
        center: Vec2,
        radius: float,
        color: Tuple[int, int, int] = (0, 0, 0),
        filled: bool = False,
    ) -> None:
        """
        Adds a circle with the specified center, radius, and color to the render queue.

        Args:
            center: The center of the circle in world space.
            radius: The radius of the circle.
            color: The color of the circle.
            filled: Whether to fill the circle.
        """
        if not self.enabled:
            return
        self._add_circle_impl(center, radius, color, filled)

    def add_polygon(
        self,
        vertices: list[Vec2],
        color: Tuple[int, int, int] = (0, 0, 0),
        filled: bool = False,
    ) -> None:
        """
        Adds a polygon defined by its vertices with the specified color to the render queue.

        Args:
            vertices: A list of Vec2 points defining the polygon's vertices in world space.
            color: The color of the polygon.
            filled: Whether to fill the polygon.
        """
        if not self.enabled:
            return
        self._add_polygon_impl(vertices, color, filled)

    def add_marker(
        self,
        position: Vec2,
        color: Tuple[int, int, int] = (255, 0, 0),
    ) -> None:
        """
        Adds a marker at the specified position with the given color to the render queue.
        Note that the size is constant and predefined and not related to the scale of the simulation.

        Args:
            position: The position of the marker in world space.
            color: The color of the marker.
        """
        if not self.enabled:
            return
        self._add_marker_impl(position, color)

    def add_marker_line(
        self,
        start: Vec2,
        direction: Vec2,
        color: Tuple[int, int, int] = (255, 0, 0),
        arrow: bool = False,
    ):
        """
        Adds a line marker starting from a position in a specified direction to the render queue.
        The size is constant and predefined.

        Args:
            start: The starting position of the line marker in world space.
            direction: The direction vector of the line marker.
            color: The color of the line marker.
            arrow: Whether to draw an arrow at the end.
        """
        if not self.enabled:
            return
        self._add_marker_line_impl(start, direction, color, arrow)

    def add_text_world(
        self,
        position: Vec2,
        text: str,
        color: Tuple[int, int, int] = (0, 0, 0),
        size: float = 12.0,
    ) -> None:
        """
        Adds text to the render queue at the specified position with the given color and size.

        Args:
            position: The position of the text in world space.
            text: The text to render.
            color: The color of the text.
            size: The font size of the text (in pixels).
        """
        if not self.enabled:
            return
        self._add_text_world_impl(position, text, color, size)

    def add_text_screen(
        self,
        position: Vec2,
        text: str,
        color: Tuple[int, int, int] = (0, 0, 0),
        size: float = 12.0,
    ) -> None:
        """
        Adds text to the render queue at the specified screen position with the given color and size.

        Args:
            position: The screen position of the text (in pixels).
            text: The text to render.
            color: The color of the text.
            size: The font size of the text (in pixels).
        """
        if not self.enabled:
            return
        self._add_text_screen_impl(position, text, color, size)

    def render_all(self) -> None:
        """
        Renders all debug graphics. Only renders if enabled.
        """
        if not self.enabled:
            return
        self._render_all_impl()

    # Abstract implementation methods that subclasses must implement
    @abstractmethod
    def _add_line_impl(
        self,
        start: Vec2,
        end: Vec2,
        color: Tuple[int, int, int],
        arrow: bool,
    ) -> None:
        """Implementation-specific line drawing."""
        pass

    @abstractmethod
    def _add_circle_impl(
        self,
        center: Vec2,
        radius: float,
        color: Tuple[int, int, int],
        filled: bool,
    ) -> None:
        """Implementation-specific circle drawing."""
        pass

    @abstractmethod
    def _add_polygon_impl(
        self,
        vertices: list[Vec2],
        color: Tuple[int, int, int],
        filled: bool,
    ) -> None:
        """Implementation-specific polygon drawing."""
        pass

    @abstractmethod
    def _add_marker_impl(
        self,
        position: Vec2,
        color: Tuple[int, int, int],
    ) -> None:
        """Implementation-specific marker drawing."""
        pass

    @abstractmethod
    def _add_marker_line_impl(
        self, start: Vec2, direction: Vec2, color: Tuple[int, int, int], arrow: bool
    ) -> None:
        """Implementation-specific marker line drawing."""
        pass

    @abstractmethod
    def _add_text_world_impl(
        self,
        position: Vec2,
        text: str,
        color: Tuple[int, int, int],
        size: float,
    ) -> None:
        """Implementation-specific world space text rendering."""
        pass

    @abstractmethod
    def _add_text_screen_impl(
        self,
        position: Vec2,
        text: str,
        color: Tuple[int, int, int],
        size: float,
    ) -> None:
        """Implementation-specific screen space text rendering."""
        pass

    @abstractmethod
    def _render_all_impl(self) -> None:
        """Implementation-specific rendering of all graphics."""
        pass

    def add_rectangle(
        self,
        position: Vec2,
        width: float,
        height: float,
        color: Tuple[int, int, int] = (0, 0, 0),
        filled: bool = False,
    ) -> None:
        """
        Adds a rectangle with the specified position, width, height, and color to the render queue.

        Args:
            position: The center of the rectangle in world space.
            width: The width of the rectangle.
            height: The height of the rectangle.
            color: The color of the rectangle.
            filled: Whether to fill the rectangle or just draw its outline.
        """
        if not self.enabled:
            return
        self._add_polygon_impl(
            [
                Vec2(position.x - width / 2, position.y - height / 2),
                Vec2(position.x + width / 2, position.y - height / 2),
                Vec2(position.x + width / 2, position.y + height / 2),
                Vec2(position.x - width / 2, position.y + height / 2),
            ],
            color=color,
            filled=filled,
        )
