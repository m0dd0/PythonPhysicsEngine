import time
import random
import logging

import pygame

from ppe.world import World
from ppe.vector import Vector
from ppe.objects import Ball, ConvexPolygon
from ppe.visualization import PyGameVisualizer

BALL_RADIUS = 0.5
BALL_INITIAL_POS = Vector(3, 3)
BOX_INITIAL_POS = Vector(5, 3)
BOX_SIZE = (1, 1)

SCREEN_DIMENSIONS_WORLD = (9, 5)
SCALE = 150
BACKGROUND_COLOR = (0, 0, 0)
OBJECT_COLOR = (255, 255, 255)
COLLISION_COLOR = (255, 0, 0)

FPS = 60
STEPS_PER_FRAME = 10
MANUAL_MOVEMENT_PER_STEP = 0.01

logging.basicConfig(level=logging.WARNING)

if __name__ == "__main__":
    box = ConvexPolygon.create_rectangle(
        pos=BOX_INITIAL_POS,
        height=BOX_SIZE[0],
        width=BOX_SIZE[1],
        style_attributes={"color": OBJECT_COLOR},
    )
    ball = Ball(
        pos=BALL_INITIAL_POS,
        radius=BALL_RADIUS,
        style_attributes={"color": OBJECT_COLOR},
    )

    world = World(
        [box, ball], world_bbox=(Vector(0, 0), Vector(*SCREEN_DIMENSIONS_WORLD))
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

        # control ball with arrow keys
        keys = pygame.key.get_pressed()
        print(keys)
        if keys[pygame.K_RIGHT]:
            ball.pos += Vector(MANUAL_MOVEMENT_PER_STEP, 0)
        elif keys[pygame.K_LEFT]:
            ball.pos += Vector(-MANUAL_MOVEMENT_PER_STEP, 0)
        elif keys[pygame.K_UP]:
            ball.pos += Vector(0, MANUAL_MOVEMENT_PER_STEP)
        elif keys[pygame.K_DOWN]:
            ball.pos += Vector(0, -MANUAL_MOVEMENT_PER_STEP)

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
                f"Warning: frame took {physic_step_duration + render_step_duration:.3f}s, "
                f"which is longer than 1/{FPS:.0f}s"
            )

        clock.tick(FPS)
