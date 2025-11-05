"""
This module defines the abstract interface for debug drawing.

Architectural Note:
The `AbstractDebugDrawer` class is intentionally placed within the `engine` package rather
than the `utils` or `view` packages. This is a critical design choice to enforce the
Dependency Inversion Principle and maintain a clean architecture. The model should be completely
independent of everything contained in the view. Since we still want to keep the debug drawing
directly in the code of the model for simplicity we consequently must keep also the
`AbstractDebugDrawer` class within the engine. This design ensures a clear separation of concerns
and decouples engine code completely from the view layer. Furthermore it prevents circular dependencies.
"""
from abc import ABC, abstractmethod
from typing import Tuple, List, Any

from ppe.engine.common import Vec2


class AbstractDebugDrawer(ABC):
    def __init__(self, enabled: bool = True):
        """
        Initializes the debug drawer.
        When one of the public methods is called the corresponding drawing command gets
        added to the internal drawing queue. This queue gets executed ones the implementation
        specific render_all method gets called.
        The queue mechanism allows us to control when the debug drawing gets executed.

        Args:
            enabled (bool): If True, debug drawing is enabled; otherwise, it is disabled.
        """
        self.enabled = enabled
        self.queue: List[Tuple[str, Tuple[Any]]] = []

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
        self.queue.append(("line", (start, end, color, arrow)))

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
        self.queue.append(("circle", center, radius, color, filled))

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
        self.queue.append(("polygon", (vertices, color, filled)))

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
        self.queue.append(("marker", (position, color)))

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
        self.queue.append(("marker_line", (start, direction, color, arrow)))

    def add_text_world(
        self,
        position: Vec2,
        text: str,
        color: Tuple[int, int, int] = (0, 0, 0),
        size: float = 12.0,
    ) -> None:
        """
        Schedules text to be drawn at a specific world position.

        The text will be anchored at the given world coordinates and will move and
        scale with the camera.

        Args:
            position (Vec2): The anchor position of the text in world coordinates.
            text (str): The string to be rendered.
            color (Tuple[int, int, int], optional): The RGB color of the text.
                Defaults to black (0, 0, 0).
            size (float, optional): The font size of the text. The final pixel size
                may be affected by the rendering backend. Defaults to 12.0.
        """
        if not self.enabled:
            return
        self.queue.append(("text_world", (position, text, color, size)))

    def add_text_screen(
        self,
        position: Vec2,
        text: str,
        color: Tuple[int, int, int] = (0, 0, 0),
        size: float = 12.0,
    ) -> None:
        """
        Schedules text to be drawn at a fixed screen position.

        The text will be anchored at the given screen coordinates (in pixels) and will
        not move or scale with the camera. This is useful for UI elements or overlays.

        Args:
            position (Vec2): The anchor position of the text in screen coordinates (pixels).
            text (str): The string to be rendered.
            color (Tuple[int, int, int], optional): The RGB color of the text.
                Defaults to black (0, 0, 0).
            size (float, optional): The font size of the text in pixels.
                Defaults to 12.0.
        """
        if not self.enabled:
            return
        self.queue.append(("text_screen", (position, text, color, size)))

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
    
    @abstractmethod
    def render_all(self) -> None:
        """
        Triggers the rendering of all scheduled debug graphics for the current frame.
        The implementation must make sure that the queued graphics are rendered and that
        the queue is cleared after rendering.

        This method should be called once per frame, after all `add_*` methods have
        been called. It will execute the backend-specific rendering implementation.
        If `enabled` is False, this method does nothing.
        """
        pass
