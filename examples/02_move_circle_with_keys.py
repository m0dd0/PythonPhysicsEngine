import logging
import time

import pygame

from ppe.world import World
from ppe.vector import Vector
from ppe.bodies import Ball, ConvexPolygon, Body
from ppe.visualization import PyGameVisualizer

logging.basicConfig(level=logging.WARNING)


SCALE = 150
DISPLAYED_AREA = Vector(9, 5)

FPS = 30
STEPS_PER_FRAME = 3


def create_bodies():
    stationary_box_1 = Body(
        shape=ConvexPolygon.create_rectangle(
            com=Vector(6, 3),
            width=1,
            height=1,
        ),
        vel=Vector(0, 0),
        acc=Vector(0, 0),
        mass=1,
        angular_vel=0,
        visual_attributes={"color": (0, 0, 0)},
        name="stationary_box",
    )

    stationary_box_2 = Body(
        ConvexPolygon.create_rectangle(
            com=Vector(4, 3),
            width=1,
            height=1,
        ),
        vel=Vector(0, 0),
        acc=Vector(0, 0),
        mass=1,
        angular_vel=0,
        visual_attributes={"color": (0, 0, 255)},
        name="moving_box",
    )

    circle = Body(
        shape=Ball(
            com=Vector(1, 3),
            radius=0.5,
        ),
        vel=Vector(1, 0),
        acc=Vector(0, 0),
        mass=1,
        angular_vel=0,
        visual_attributes={"color": (0, 255, 0)},
        name="circle",
    )

    return stationary_box_1, stationary_box_2, circle


if __name__ == "__main__":
    stationary_box_1, stationary_box_2, circle = create_bodies()
    world = World([stationary_box_1, stationary_box_2, circle])

    screen = pygame.display.set_mode(
        (int(DISPLAYED_AREA.x * SCALE), int(DISPLAYED_AREA.y * SCALE))
    )
    visualizer = PyGameVisualizer(screen, scale=SCALE)

    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        physic_step_start = time.perf_counter()
        for _ in range(STEPS_PER_FRAME):
            world.update(1 / (FPS * STEPS_PER_FRAME))
        physic_step_duration = time.perf_counter() - physic_step_start

        screen.fill((255, 255, 255))
        visualizer.draw(world, draw_bbox=True)
        pygame.display.flip()

        if physic_step_duration > 1 / FPS:
            logging.warning(f"Warning: frame took {physic_step_duration}s, ")

        clock.tick(FPS)
