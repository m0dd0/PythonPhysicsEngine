from typing import Any, List
from abc import ABC, abstractmethod

import pygame

from ppe.objects import GameObject, Ball, Polygon
from ppe import collision


class World:
    def __init__(self, objects: List[GameObject]):
        self.objects = objects

    def update(self, dt: float):
        for obj in self.objects:
            obj.update(dt)

        collisions = collision.get_collisions(self.objects)
        for c in collisions:
            # TODO handle collison: update velocities
            pass


class Visualizer(ABC):
    def __init__(self, world: World):
        self.world = world

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
    def __init__(self, world: World, screen: pygame.Surface):
        super().__init__(world)
        self.screen = screen

    def draw_ball(self, ball: Ball):
        pygame.draw.circle(
            self.screen,
            ball.color,
            (int(ball.pos.x), int(ball.pos.y)),
            ball.radius,
        )

    def draw_polygon(self, polygon: Polygon):
        pygame.draw.polygon(
            self.screen,
            polygon.color,
            [(v.x, v.y) for v in polygon.vertices],
        )


if __name__ == "__main__":
    from ppe.vector import Vector
    import math

    ball = Ball(
        Vector(400, 300),
        Vector(0, 0),
        Vector(0, 0),
        1,
        False,
        (255, 255, 255),
    )
    world = World([ball])

    FPS = 60
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((800, 600))

    visualizer = PyGameVisualizer(world, screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        world.update(1 / FPS)

        screen.fill((0, 0, 0))
        visualizer.draw()

        clock.tick(FPS)
