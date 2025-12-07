"""
This module defines tools for graphical debugging.
"""

from typing import Any, List, Tuple

from ppe.engine.common import Vec2


class DebugRecorder:
    def __init__(self, enabled: bool = True):
        """
        Initializes the debug drawer.
        When one of the public methods is called the corresponding drawing command gets
        added to the internal drawing queue. This queue can be read by a view mplementation
        and visualized on the screen.
        The queue mechanism allows us to control when the debug drawing gets executed.
        I.e. the debug visuals are not overlapped with the game visuals.

        Args:
            enabled (bool): If True, debug drawing is enabled; otherwise, it is disabled.
        """
        self.enabled = enabled

        # command_queue is a list of commans-commandArgs tuples: [("line", (start, end, color, arrow)), ...]
        self.command_queue: List[Tuple[str, Tuple[Any]]] = []

    def add_line(
        self,
        start: Vec2,
        end: Vec2,
        color: Tuple[int, int, int] = (0, 0, 0),
        arrow: bool = False,
    ) -> None:
        """
        Schedules a line to be drawn in the next rendering pass.

        This method adds a line segment, defined by its start and end points in world
        coordinates, to the internal drawing queue. An optional arrow can be added
        at the end of the line.

        Args:
            start (Vec2): The starting point of the line in world coordinates.
            end (Vec2): The ending point of the line in world coordinates.
            color (Tuple[int, int, int], optional): The RGB color of the line.
                Defaults to black (0, 0, 0).
            arrow (bool, optional): If True, an arrowhead will be drawn at the `end`
                of the line. Defaults to False.
        """
        if not self.enabled:
            return
        self.command_queue.append(("line", (start, end, color, arrow)))

    def add_circle(
        self,
        center: Vec2,
        radius: float,
        color: Tuple[int, int, int] = (0, 0, 0),
        filled: bool = False,
    ) -> None:
        """
        Schedules a circle to be drawn in the next rendering pass.

        This method adds a circle, defined by its center and radius in world coordinates,
        to the internal drawing queue.

        Args:
            center (Vec2): The center of the circle in world coordinates.
            radius (float): The radius of the circle in world units (meters).
            color (Tuple[int, int, int], optional): The RGB color of the circle.
                Defaults to black (0, 0, 0).
            filled (bool, optional): If True, the circle is drawn filled; otherwise,
                only its outline is drawn. Defaults to False.
        """
        if not self.enabled:
            return
        self.command_queue.append(("circle", center, radius, color, filled))

    def add_polygon(
        self,
        vertices: list[Vec2],
        color: Tuple[int, int, int] = (0, 0, 0),
        filled: bool = False,
    ) -> None:
        """
        Schedules a polygon to be drawn in the next rendering pass.

        This method adds a polygon, defined by a list of vertices in world coordinates,
        to the internal drawing queue.

        Args:
            vertices (list[Vec2]): A list of `Vec2` points defining the polygon's
                vertices in world coordinates, in order.
            color (Tuple[int, int, int], optional): The RGB color of the polygon.
                Defaults to black (0, 0, 0).
            filled (bool, optional): If True, the polygon is drawn filled; otherwise,
                only its outline is drawn. Defaults to False.
        """
        if not self.enabled:
            return
        self.command_queue.append(("polygon", (vertices, color, filled)))

    def add_marker(
        self,
        position: Vec2,
        color: Tuple[int, int, int] = (255, 0, 0),
    ) -> None:
        """
        Schedules a fixed-size marker to be drawn at a world position.

        This is useful for highlighting specific points of interest. The marker's size
        is constant in screen space, meaning it does not scale with camera zoom.

        Args:
            position (Vec2): The position of the marker in world coordinates.
            color (Tuple[int, int, int], optional): The RGB color of the marker.
                Defaults to red (255, 0, 0).
        """
        if not self.enabled:
            return
        self.command_queue.append(("marker", (position, color)))

    def add_marker_line(
        self,
        start: Vec2,
        direction: Vec2,
        color: Tuple[int, int, int] = (255, 0, 0),
        arrow: bool = False,
    ):
        """
        Schedules a fixed-length line marker from a point in a given direction.

        This is useful for visualizing vectors like forces or velocities. The line's
        length is constant in screen space, meaning it does not scale with camera zoom.

        Args:
            start (Vec2): The starting position of the line in world coordinates.
            direction (Vec2): The direction vector of the line. The length of this
                vector does not affect the rendered line's length.
            color (Tuple[int, int, int], optional): The RGB color of the line.
                Defaults to red (255, 0, 0).
            arrow (bool, optional): If True, an arrowhead is drawn at the end.
                Defaults to False.
        """
        if not self.enabled:
            return
        self.command_queue.append(("marker_line", (start, direction, color, arrow)))

    def add_rectangle(
        self,
        position: Vec2,
        width: float,
        height: float,
        color: Tuple[int, int, int] = (0, 0, 0),
        filled: bool = False,
    ) -> None:
        """
        A convenience method to schedule a rectangle to be drawn.

        This method calculates the four vertices of a rectangle and schedules it for
        drawing as a polygon.

        Args:
            position (Vec2): The center of the rectangle in world coordinates.
            width (float): The width of the rectangle in world units.
            height (float): The height of the rectangle in world units.
            color (Tuple[int, int, int], optional): The RGB color of the rectangle.
                Defaults to black (0, 0, 0).
            filled (bool, optional): If True, the rectangle is drawn filled;
                otherwise, only its outline is drawn. Defaults to False.
        """
        if not self.enabled:
            return
        self.add_polygon(
            [
                Vec2(position.x - width / 2, position.y - height / 2),
                Vec2(position.x + width / 2, position.y - height / 2),
                Vec2(position.x + width / 2, position.y + height / 2),
                Vec2(position.x - width / 2, position.y + height / 2),
            ],
            color=color,
            filled=filled,
        )
