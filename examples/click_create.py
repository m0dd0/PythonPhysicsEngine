import time
import random
import logging

import pygame

from ppe.world import World
from ppe.vector import Vector
from ppe.bodies import Ball, ConvexPolygon
from ppe.visualization import PyGameVisualizer

RADIUS_BOUNDS = (0.1, 0.3)
RECTANGLE_SIDE_BOUNDS = (0.1, 0.5)
FLOOR_VERTICES = [Vector(2, 1), Vector(2, 1.2), Vector(7, 1.2), Vector(7, 1)]
GRAVIY = Vector(0, -9.81)
BOUNCINESS = 0.8

SCREEN_DIMENSIONS_WORLD = (9, 5)
SCALE = 150
BACKGROUND_COLOR = (255, 255, 255)
OBJECT_COLORS = ["#ffbe0b", "#fb5607", "#ff006e", "#8338ec", "#3a86ff"]

FPS = 60
STEPS_PER_FRAME = 10

logging.basicConfig(level=logging.WARNING)

if __name__ == "__main__":
    floor = ConvexPolygon(
        vertices=FLOOR_VERTICES,
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
        (SCREEN_DIMENSIONS_WORLD[0] * SCALE, SCREEN_DIMENSIONS_WORLD[1] * SCALE)
    )
    visualizer = PyGameVisualizer(screen, scale=SCALE)

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
                            height=random.uniform(*RECTANGLE_SIDE_BOUNDS),
                            width=random.uniform(*RECTANGLE_SIDE_BOUNDS),
                            style_attributes={"color": random.choice(OBJECT_COLORS)},
                            acc=GRAVIY,
                            bounciness=BOUNCINESS,
                        )
                    )
                elif event.button == 3:  # right click
                    world.bodies.append(
                        Ball(
                            pos=visualizer.pixel_2_world_coord(Vector(x, y)),
                            radius=random.uniform(*RADIUS_BOUNDS),
                            style_attributes={"color": random.choice(OBJECT_COLORS)},
                            acc=GRAVIY,
                            bounciness=BOUNCINESS,
                        )
                    )

        physic_step_start = time.perf_counter()
        for _ in range(STEPS_PER_FRAME):
            world.update(1 / (FPS * STEPS_PER_FRAME))
        physic_step_duration = time.perf_counter() - physic_step_start

        render_step_start = time.perf_counter()
        screen.fill(BACKGROUND_COLOR)
        visualizer.draw(world)
        pygame.display.flip()
        render_step_duration = time.perf_counter() - render_step_start

        logging.info(f"{physic_step_duration:.3f}s, {render_step_duration:.3f}s")
        if physic_step_duration + render_step_duration > 1 / FPS:
            logging.warning(
                f"Warning: frame took {physic_step_duration:.3f} + {render_step_duration:.3f} = {physic_step_duration + render_step_duration:.3f}s, "
                f"which is longer than 1/{FPS:.0f}s = {1/FPS:.3f}s."
            )

        clock.tick(FPS)
