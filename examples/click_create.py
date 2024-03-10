import time
import random
import logging
from typing import Tuple

import pygame

from ppe.world import World
from ppe.vector import Vector
from ppe.bodies import Ball, ConvexPolygon
from ppe.visualization import PyGameVisualizer

GRAVIY = Vector(0, -9.81)
BOUNCINESS = 0.8

SCREEN_DIMENSIONS_WORLD = (9, 5)
OBJECT_COLORS = ["#ffbe0b", "#fb5607", "#ff006e", "#8338ec", "#3a86ff"]

FPS = 60
STEPS_PER_FRAME = 10

logging.basicConfig(level=logging.WARNING)


def setup(
    scale, screen_dimensions_world, background_color
) -> Tuple[World, PyGameVisualizer]:
    floor = ConvexPolygon(
        vertices=[Vector(2, 1), Vector(2, 1.2), Vector(7, 1.2), Vector(7, 1)],
        vel=Vector(0, 0),
        acc=Vector(0, 0),
        mass=float("inf"),
        angular_vel=0,
        fixed=True,
        style_attributes={"color": (0, 0, 0)},
        name="floor",
        bounciness=BOUNCINESS,
    )

    world = World([floor], world_bbox=(Vector(0, 0), Vector(*SCREEN_DIMENSIONS_WORLD)))

    screen = pygame.display.set_mode(
        (screen_dimensions_world[0] * scale, screen_dimensions_world[1] * scale)
    )
    visualizer = PyGameVisualizer(screen, background_color, scale=scale)

    return world, visualizer


if __name__ == "__main__":
    world, visualizer = setup(150, (9, 5), (255, 255, 255))

    clock = pygame.time.Clock()

    running = True
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if event.button == 1:  # left click
                    world.bodies.append(
                        ConvexPolygon.create_rectangle(
                            pos=visualizer.pixel_2_world_coord(Vector(x, y)),
                            height=random.uniform(0.1, 0.5),
                            width=random.uniform(0.1, 0.5),
                            style_attributes={"color": random.choice(OBJECT_COLORS)},
                            acc=GRAVIY,
                            bounciness=BOUNCINESS,
                        )
                    )
                elif event.button == 3:  # right click
                    world.bodies.append(
                        Ball(
                            pos=visualizer.pixel_2_world_coord(Vector(x, y)),
                            radius=random.uniform(0.1, 0.3),
                            style_attributes={"color": random.choice(OBJECT_COLORS)},
                            acc=GRAVIY,
                            bounciness=BOUNCINESS,
                        )
                    )

        physic_step_start = time.perf_counter()
        for _ in range(STEPS_PER_FRAME):
            # substepping (multiple physics steps per frame)
            world.update(1 / (FPS * STEPS_PER_FRAME))
        physic_step_duration = time.perf_counter() - physic_step_start

        render_step_start = time.perf_counter()
        visualizer.draw(world)
        pygame.display.flip()
        render_step_duration = time.perf_counter() - render_step_start

        logging.info(
            f"frame time: {1/FPS}, physic step: {physic_step_duration:.3f}s, render step: {render_step_duration:.3f}s"
        )

        clock.tick(FPS)
