import time

import pygame
from palettable.cartocolors.diverging import Earth_5

from ppe.world import World
from ppe.vector import Vector
from ppe.objects import Ball, ConvexPolygon
from ppe.visualization import PyGameVisualizer

RADIUS_BOUNDS = (0.1, 0.3)
RECTANGLE_SIDE_BOUNDS = (0.1, 0.5)

FLOOR_VERTICES = [Vector(2, 1), Vector(2, 1.2), Vector(7, 1.2), Vector(7, 1)]

SCREEN_DIMENSIONS_WORLD = (9, 5)
SCALE = 150
BACKGROUND_COLOR = Earth_5.colors[2]
OBJECT_COLOR = Earth_5.colors.copy()
OBJECT_COLOR.remove(BACKGROUND_COLOR)

FPS = 60
STEPS_PER_FRAME = 1


if __name__ == "__main__":
    floor = ConvexPolygon(
        vertices=FLOOR_VERTICES,
        vel=Vector(0, 0),
        acc=Vector(0, 0),
        mass=float("inf"),
        angular_vel=0,
        fixed=True,
        color=(0, 0, 0),
        name="floor",
    )

    world = World([floor])

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

        print(f"{physic_step_duration:.3f}s, {render_step_duration:.3f}s")
        if physic_step_duration + render_step_duration > 1 / FPS:
            print(
                f"Warning: frame took {physic_step_duration + render_step_duration:.3f}s, "
                f"which is longer than 1/{FPS:.0f}s"
            )

        clock.tick(FPS)
