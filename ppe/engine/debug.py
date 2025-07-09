from abc import ABC, abstractmethod

from ppe.engine.core import Vec2

class AbstractDebugDrawer(ABC):
    """An abstract base class for all debug drawer strategies."""

    @abstractmethod
    def draw_line(self, start: Vec2, end: Vec2, color: str) -> None:
        """
        Draws a line from start to end with the specified color.

        Args:
            start: The starting point of the line in world space.
            end: The ending point of the line in world space.
            color: The color of the line.
        """
        pass

    @abstractmethod
    def draw_circle(self, center: Vec2, radius: float, color: str) -> None:
        """
        Draws a circle with the specified center, radius, and color.

        Args:
            center: The center of the circle in world space.
            radius: The radius of the circle.
            color: The color of the circle.
        """
        pass

    @abstractmethod
    def draw_polygon(self, vertices: list[Vec2], color: str) -> None:
        """
        Draws a polygon defined by its vertices with the specified color.

        Args:
            vertices: A list of Vec2 points defining the polygon's vertices in world space.
            color: The color of the polygon.
        """
        pass