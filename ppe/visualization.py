from abc import ABC, abstractmethod
from typing import Any, Dict

import pygame

from ppe.world import World
from ppe.bodies import Ball, ConvexPolygon
from ppe.vector import Vector


class Visualizer(ABC):
    def __init__(self, scale: float = 100, viewport_offset: Vector = None):
        self.scale = scale
        self.viewport_offset = viewport_offset or Vector(0, 0)

    @abstractmethod
    def draw_ball(self, ball: Ball, visual_attributes: Dict[Any, Any]):
        raise NotImplementedError()

    @abstractmethod
    def draw_polygon(self, polygon: ConvexPolygon, visual_attributes: Dict[Any, Any]):
        raise NotImplementedError()

    def draw(self, world: World):
        for body in world.bodies:
            if isinstance(body.shape, Ball):
                self.draw_ball(body.shape, body.visual_attributes)
            elif isinstance(body.shape, ConvexPolygon):
                self.draw_polygon(body.shape, body.visual_attributes)
            else:
                raise ValueError(f"Unknown object type {type(body)}")

    @abstractmethod
    def pixel_2_world_coord(self, pos: Vector) -> Vector:
        raise NotImplementedError()

    @abstractmethod
    def world_2_pixel_coord(self, pos: Vector) -> Vector:
        raise NotImplementedError()


class PyGameVisualizer(Visualizer):
    def __init__(
        self,
        screen: pygame.Surface,
        scale: float = 100,
        viewport_offset=None,
    ):
        super().__init__(scale, viewport_offset)
        self.screen = screen

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

    def draw_ball(self, ball: Ball, visual_attributes: Dict[Any, Any]):
        pygame.draw.circle(
            self.screen,
            visual_attributes["color"],
            self.world_2_pixel_coord(ball.pos).to_tuple(),
            ball.radius * self.scale,
        )

    def draw_polygon(self, polygon: ConvexPolygon, visual_attributes: Dict[Any, Any]):
        pygame.draw.polygon(
            self.screen,
            visual_attributes["color"],
            [self.world_2_pixel_coord(v).to_tuple() for v in polygon.vertices],
        )
