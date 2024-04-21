from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

import pygame

from ppe.world import World
from ppe.bodies import Ball, ConvexPolygon, Body
from ppe.vector import Vector
from ppe.collision.collision_data import Collision


class Visualizer(ABC):
    """This is the abstract base class for all visualizers. Different visualizers can be
    implemented by inheriting from this class and implementing the abstract methods with
    a specific visualization library. For example, PyGameVisualizer is a concrete class.
    To allow as much feeedom as possible for the drawing process only a few methods are
    defined here. Note that the visualizer is responsible for converting between world
    coordinates and pixel coordinates. This is necessary because the physics engine
    operates in meters, but the visualizer operates in pixels.
    """

    def __init__(self, scale: float = 100, viewport_offset: Vector = None):
        """Initializes the visualizer.

        Args:
            scale (float, optional): The scale factor to convert between world and pixel
                coordinates. Defaults to 100. This means that 1 meter in the world is
                represented by 100 pixels on the screen.
            viewport_offset (Vector, optional): The offset of the viewport in world
                coordinates. Defaults to the origin (0, 0) in the world.
        """
        self.scale = scale
        self.viewport_offset = viewport_offset or Vector(0, 0)

    @abstractmethod
    def draw(
        self, world: World, draw_bbox: bool = False, draw_contact_manifold: bool = False
    ) -> None:
        """Draws the world and optionally debug information like bounding boxes and contact
        manifolds.

        Args:
            world (World): The world to draw.
            draw_bbox (bool, optional): Whether to draw the bounding boxes of the bodies.
                Defaults to False.
            draw_contact_manifold (bool, optional): Whether to draw the contact manifold
                of the bodies. Defaults to False.
        """
        raise NotImplementedError()

    @abstractmethod
    def pixel_2_world_coord(self, pos: Vector) -> Vector:
        """Converts pixel coordinates to world coordinates.

        Args:
            pos (Vector): The pixel coordinates.

        Returns:
            Vector: The world coordinates.
        """
        raise NotImplementedError()

    @abstractmethod
    def world_2_pixel_coord(self, pos: Vector) -> Vector:
        """Converts world coordinates to pixel coordinates.

        Args:
            pos (Vector): The world coordinates.

        Returns:
            Vector: The pixel coordinates.
        """
        raise NotImplementedError()


class PyGameVisualizer(Visualizer):
    def __init__(
        self,
        screen: pygame.Surface,
        background_color: Tuple = (255, 255, 255),
        scale: float = 100,
        viewport_offset: Vector = None,
    ):
        """Initializes the PyGame visualizer. The PyGame visulaizer draws the world using
        the PyGame library and can draw on an arbitrary PyGame surface.

        Args:
            screen (pygame.Surface): The PyGame surface to draw on.
            background_color (Tuple, optional): The background color of the screen.
                Defaults to (255, 255, 255).
            scale (float, optional): The scale factor to convert between world and pixel
                coordinates. Defaults to 100. This means that 1 meter in the world is
                represented by 100 pixels on the screen.
            viewport_offset (Vector, optional): The offset of the viewport in world
                coordinates. Defaults to the origin (0, 0) in the world.
        """
        super().__init__(scale, viewport_offset)
        self.screen = screen
        self.backgound_color = background_color

        self._bbox_color = (0, 0, 0)
        self._bbox_thickness = 1
        self._collision_manifold_color = (255, 0, 0)
        self._collision_point_size = 10

    def world_2_pixel_coord(self, pos: Vector) -> Vector:
        pos = pos - self.viewport_offset  # coordinates in meters relative to viewport
        pos = pos * self.scale  # coordinates in pixels relative to viewport
        pos = Vector(pos.x, self.screen.get_height() - pos.y)  # flip y axis

        return pos

    def pixel_2_world_coord(self, pos: Vector) -> Vector:
        pos = Vector(pos.x, self.screen.get_height() - pos.y)
        pos = pos / self.scale
        pos = pos + self.viewport_offset

        return pos

    def _draw_ball(self, ball: Ball, visual_attributes: Dict[Any, Any]):
        pygame.draw.circle(
            self.screen,
            visual_attributes["color"],
            self.world_2_pixel_coord(ball.com).to_tuple(),
            ball.radius * self.scale,
        )
        if not visual_attributes.get("rotation_line", False):
            pygame.draw.line(
                self.screen,
                start_pos=self.world_2_pixel_coord(ball.com).to_tuple(),
                end_pos=self.world_2_pixel_coord(ball.vertices[1]).to_tuple(),
                color=visual_attributes.get("rotation_line_color", (0, 0, 0)),
                width=visual_attributes.get("rotation_line_width", 1),
            )

    def _draw_polygon(self, polygon: ConvexPolygon, visual_attributes: Dict[Any, Any]):
        pygame.draw.polygon(
            self.screen,
            visual_attributes["color"],
            [self.world_2_pixel_coord(v).to_tuple() for v in polygon.vertices],
        )

    def _draw_bbox(self, body: Body):
        bottom, left = body.shape.bbox[0].to_tuple()
        top, right = body.shape.bbox[1].to_tuple()

        pygame.draw.polygon(
            self.screen,
            self._bbox_color,
            [
                self.world_2_pixel_coord(Vector(top, left)).to_tuple(),
                self.world_2_pixel_coord(Vector(top, right)).to_tuple(),
                self.world_2_pixel_coord(Vector(bottom, right)).to_tuple(),
                self.world_2_pixel_coord(Vector(bottom, left)).to_tuple(),
            ],
            self._bbox_thickness,
        )

    def _draw_contact_manifold(self, collision: Collision):
        pygame.draw.circle(
            self.screen,
            self._collision_manifold_color,
            # collision.penetrating_point
            self.world_2_pixel_coord(collision.penetrating_point).to_tuple(),
            self._collision_point_size,
        )

    def draw(
        self, world: World, draw_bbox: bool = False, draw_contact_manifold: bool = False
    ):
        self.screen.fill(self.backgound_color)

        for body in world.bodies:
            if isinstance(body.shape, Ball):
                self._draw_ball(body.shape, body.visual_attributes)
            elif isinstance(body.shape, ConvexPolygon):
                self._draw_polygon(body.shape, body.visual_attributes)
            else:
                raise ValueError(f"Unknown object type {type(body)}")

        if draw_bbox:
            for body in world.bodies:
                self._draw_bbox(body)

        if draw_contact_manifold:
            for collision in world.collisions:
                self._draw_contact_manifold(collision)
