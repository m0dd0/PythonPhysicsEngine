from typing import Any, List
from abc import ABC, abstractmethod

import pygame

from ppe.objects import GameObject, Ball, Polygon
from ppe import collision
from ppe.vector import Vector


class World:
    def __init__(self, objects: List[GameObject]):
        self.objects = objects

    def update(self, dt: float):
        for obj in self.objects:
            obj.update(dt)

        collisions = collision.get_collisions(self.objects)
        for c in collisions:
            # TODO handle collison: update velocities
            c.obj1.color = (255, 0, 0)
            c.obj2.color = (255, 0, 0)


class Visualizer(ABC):
    def __init__(
        self, world: World, scale: float = 100, viewport_offset: Vector = None
    ):
        self.world = world
        self.scale = scale
        self.viewport_offset = viewport_offset or Vector(0, 0)

    @abstractmethod
    def draw_ball(self, ball: Any):
        raise NotImplementedError()

    @abstractmethod
    def draw_polygon(self, polygon: Any):
        raise NotImplementedError()

    def draw(self):
        for obj in self.world.objects:
            if isinstance(obj, Ball):
                self.draw_ball(obj)
            elif isinstance(obj, Polygon):
                self.draw_polygon(obj)
            else:
                raise ValueError(f"Unknown object type {type(obj)}")


class PyGameVisualizer(Visualizer):
    def __init__(
        self,
        world: World,
        screen: pygame.Surface,
        scale: float = 100,
        viewport_offset=None,
    ):
        super().__init__(world, scale, viewport_offset)
        self.screen = screen

    def _world_to_screen(self, pos: Vector) -> Vector:
        pos = pos - self.viewport_offset  # coordinates in meters relative to viewport
        pos = pos * self.scale  # coordinates in pixels relative to viewport
        pos.y = self.screen.get_height() - pos.y  # flip y axis
        return pos

    def draw_ball(self, ball: Ball):
        pygame.draw.circle(
            self.screen,
            ball.color,
            self._world_to_screen(ball.pos).to_tuple(),
            ball.radius * self.scale,
        )

    def draw_polygon(self, polygon: Polygon):
        pygame.draw.polygon(
            self.screen,
            polygon.color,
            [self._world_to_screen(v).to_tuple() for v in polygon.vertices],
        )


if __name__ == "__main__":
    from ppe.vector import Vector
    import math

    ball = Ball(
        Vector(0, 0),
        Vector(0, 0),
        Vector(0, 0),
        1,
        0.05,
        False,
        (255, 255, 255),
    )
    rectangle = Polygon(
        Vector(0, 0),
        Vector(0, 0),
        Vector(0, 0),
        math.inf,
        [
            Vector(0.25, 1),
            Vector(0.25, 1.1),
            Vector(0.75, 1.1),
            Vector(0.75, 1),
        ],
        True,
        (255, 255, 255),
    )
    world = World([ball, rectangle])

    FPS = 60
    SCALE = 300
    SCREEN_WIDTH_METER = 1
    SCREEN_HEIGHT_METER = 2

    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH_METER * SCALE, SCREEN_HEIGHT_METER * SCALE)
    )

    visualizer = PyGameVisualizer(world, screen, scale=SCALE)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # control ball position with arrow keys
        # move 0.01 meters per frame
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            ball.pos.x -= 0.01
        if keys[pygame.K_RIGHT]:
            ball.pos.x += 0.01
        if keys[pygame.K_UP]:
            ball.pos.y += 0.01
        if keys[pygame.K_DOWN]:
            ball.pos.y -= 0.01

        world.update(1 / FPS)

        screen.fill((0, 0, 0))
        visualizer.draw()
        pygame.display.flip()

        clock.tick(FPS)
