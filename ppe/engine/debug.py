from abc import ABC, abstractmethod
from typing import Tuple

from ppe.engine.common import Vec2


class AbstractDebugDrawer(ABC):
    """An abstract base class for all debug drawer strategies."""

    @abstractmethod
    def draw_line(
        self,
        start: Vec2,
        end: Vec2,
        color: Tuple[int, int, int] = (0, 0, 0),
        arrow: bool = False,
    ) -> None:
        """
        Draws a line from start to end with the specified color.

        Args:
            start: The starting point of the line in world space.
            end: The ending point of the line in world space.
            color: The color of the line.
        """
        pass

    @abstractmethod
    def draw_circle(
        self,
        center: Vec2,
        radius: float,
        color: Tuple[int, int, int] = (0, 0, 0),
        filled: bool = False,
    ) -> None:
        """
        Draws a circle with the specified center, radius, and color.

        Args:
            center: The center of the circle in world space.
            radius: The radius of the circle.
            color: The color of the circle.
        """
        pass

    @abstractmethod
    def draw_polygon(
        self,
        vertices: list[Vec2],
        color: Tuple[int, int, int] = (0, 0, 0),
        filled: bool = False,
    ) -> None:
        """
        Draws a polygon defined by its vertices with the specified color.

        Args:
            vertices: A list of Vec2 points defining the polygon's vertices in world space.
            color: The color of the polygon.
        """
        pass

    @abstractmethod
    def draw_marker(
        self,
        position: Vec2,
        color: Tuple[int, int, int] = (255, 0, 0),
    ) -> None:
        """
        Draws a marker at the specified position with the given color.
        Note that the size is constant and predefined and not related to the scale of the simulation.

        Args:
            position: The position of the marker in world space.
            size: The size of the marker.
            color: The color of the marker.
        """
        pass


    def draw_rectangle(
        self,
        position: Vec2,
        width: float,
        height: float,
        color: Tuple[int, int, int] = (0, 0, 0),
        filled: bool = False,
    ) -> None:
        """
        Draws a rectangle with the specified position, width, height, and color.

        Args:
            position: The center of the rectangle in world space.
            width: The width of the rectangle.
            height: The height of the rectangle.
            angle: The rotation angle of the rectangle in radians.
            color: The color of the rectangle.
            filled: Whether to fill the rectangle or just draw its outline.
        """
        self.draw_polygon(
            [
                Vec2(position.x - width / 2, position.y - height / 2),
                Vec2(position.x + width / 2, position.y - height / 2),
                Vec2(position.x + width / 2, position.y + height / 2),
                Vec2(position.x - width / 2, position.y + height / 2),
            ],
            color=color,
            filled=filled,
        )