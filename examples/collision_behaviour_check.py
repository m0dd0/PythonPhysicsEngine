import time
import logging
import math

import pygame

from ppe.world import World
from ppe.vector import Vector
from ppe.objects import Ball, ConvexPolygon
from ppe.visualization import PyGameVisualizer

STATIONARY_BOX_POS = Vector(5, 3)
STATIONARY_BOX_SIZE = (1, 1)
STATIONARY_BOX_COLOR = (0, 255, 0)
MOVING_BOX_INITIAL_POS = Vector(1, 3)
MOVING_BOX_SIZE = (1, 1)
MOVING_BOX_COLOR = (0, 0, 255)

SCREEN_DIMENSIONS_WORLD = (9, 5)
SCALE = 150
BACKGROUND_COLOR = (0, 0, 0)

FPS = 60
STEPS_PER_FRAME = 10

logging.basicConfig(level=logging.WARNING)


if __name__ == "__main__":
    stationary_box = ConvexPolygon.create_rectangle(
        pos=STATIONARY_BOX_POS,
        width=STATIONARY_BOX_SIZE[0],
        height=STATIONARY_BOX_SIZE[1],
        vel=Vector(0.5, 0),
        acc=Vector(0, 0),
        mass=float("inf"),
        angular_vel=0,
        fixed=True,
        style_attributes={"color": STATIONARY_BOX_COLOR},
        name="stationary_box",
    )
    moving_box = ConvexPolygon.create_rectangle(
        pos=MOVING_BOX_INITIAL_POS,
        width=MOVING_BOX_SIZE[0],
        height=MOVING_BOX_SIZE[1],
        vel=Vector(2, 0),
        acc=Vector(0, 0),
        mass=1,
        angular_vel=0,
        fixed=True,
        style_attributes={"color": MOVING_BOX_COLOR},
        name="moving_box",
    )
    world = World(
        [stationary_box, moving_box],
        world_bbox=(Vector(0, 0), Vector(*SCREEN_DIMENSIONS_WORLD)),
    )

    screen = pygame.display.set_mode(
        (SCREEN_DIMENSIONS_WORLD[0] * SCALE, SCREEN_DIMENSIONS_WORLD[1] * SCALE)
    )
    visualizer = PyGameVisualizer(world, screen, scale=SCALE)

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

        render_step_start = time.perf_counter()
        screen.fill(BACKGROUND_COLOR)
        visualizer.draw()
        pygame.display.flip()
        render_step_duration = time.perf_counter() - render_step_start

        logging.info(f"{physic_step_duration:.3f}s, {render_step_duration:.3f}s")
        if physic_step_duration + render_step_duration > 1 / FPS:
            logging.warning(
                f"Warning: frame took {physic_step_duration} + {render_step_duration:.3f} = {physic_step_duration + render_step_duration:.3f}s, "
                f"which is longer than 1/{FPS:.0f}s = {1/FPS:.3f}s."
            )

        clock.tick(FPS)
