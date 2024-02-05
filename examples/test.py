import time

import pygame

from ppe.world import World
from ppe.vector import Vector
from ppe.objects import Ball, ConvexPolygon

WORLD_DIMENSIONS = (3, 3)
OBJECT_SIZE_BOUNDS = (0.1, 0.5)
N_BALLS = 5
N_POLYGONS = 5
N_VERTICES_BOUNDS = (3, 5)
MASS_BOUNDS = (1, 1)

SCREEN_DIMENSIONS = (600, 600)
if __name__ == "__main__":
    polygons = [
        ConvexPolygon.create_random(
            (Vector(0, 0), Vector(*WORLD_DIMENSIONS)),
            OBJECT_SIZE_BOUNDS,
            N_VERTICES_BOUNDS,
            MASS_BOUNDS,
        )
        for _ in range(N_POLYGONS)
    ]

    balls = [
        Ball.create_random(
            (Vector(0, 0), Vector(*WORLD_DIMENSIONS)),
            OBJECT_SIZE_BOUNDS,
            MASS_BOUNDS,
        )
        for _ in range(N_BALLS)
    ]

    world = World(polygons + balls)

    screen = pygame.display.set_mode(SCREEN_DIMENSIONS)
    visualizer = PyGameVisualizer(world, screen)

    # ball_small = Ball(
    #     Vector(0, 0),
    #     Vector(0, 0),
    #     Vector(0, 0),
    #     0,
    #     0,
    #     1,
    #     0.05,
    #     False,
    #     (255, 255, 255),
    #     name="ball_small",
    # )
    # ball_big = Ball(
    #     Vector(0.5, 1),
    #     Vector(0, 0),
    #     Vector(0, 0),
    #     0,
    #     0,
    #     1,
    #     0.2,
    #     False,
    #     (255, 255, 255),
    #     name="ball_big",
    # )
    # rectangle_small = ConvexPolygon(
    #     Vector(0, 0),
    #     Vector(0, 0),
    #     0,
    #     0,
    #     1,
    #     [
    #         Vector(0, 0),
    #         Vector(0, 0.1),
    #         Vector(0.1, 0.1),
    #         Vector(0.1, 0),
    #     ],
    #     False,
    #     (255, 255, 255),
    #     name="rectangle_small",
    # )
    # rectangle_big = ConvexPolygon(
    #     Vector(0, 0),
    #     Vector(0, 0),
    #     0,
    #     0,
    #     1,
    #     [
    #         Vector(0.25, 0.75),
    #         Vector(0.25, 1.25),
    #         Vector(0.75, 1.25),
    #         Vector(0.75, 0.75),
    #     ],
    #     False,
    #     (255, 255, 255),
    #     name="rectangle_big",
    # )

    # # world = World([ball, ball2])
    # world = World([rectangle_big, ball_small])
    # controlled_object = ball_small

    # FPS = 60
    # SCALE = 300
    # SCREEN_WIDTH_METER = 1
    # SCREEN_HEIGHT_METER = 2

    # pygame.init()
    # screen = pygame.display.set_mode(
    #     (SCREEN_WIDTH_METER * SCALE, SCREEN_HEIGHT_METER * SCALE)
    # )

    # visualizer = PyGameVisualizer(world, screen, scale=SCALE)

    # running = True
    # last_input_check = time.time()
    # last_update = time.time()
    # while running:
    #     current_time = time.time()
    #     if current_time - last_input_check >= 1 / FPS:
    #         # check user input
    #         for event in pygame.event.get():
    #             if event.type == pygame.QUIT:
    #                 running = False

    #         keys = pygame.key.get_pressed()
    #         if keys[pygame.K_LEFT]:
    #             controlled_object.move_by(Vector(-0.01, 0))
    #         if keys[pygame.K_RIGHT]:
    #             controlled_object.move_by(Vector(0.01, 0))
    #         if keys[pygame.K_UP]:
    #             controlled_object.move_by(Vector(0, 0.01))
    #         if keys[pygame.K_DOWN]:
    #             controlled_object.move_by(Vector(0, -0.01))

    #         last_input_check = current_time

    #     # update game logic as often as possible
    #     delta = current_time - last_update
    #     world.update(delta)

    #     # render
    #     screen.fill((0, 0, 0))
    #     visualizer.draw()
    #     pygame.display.flip()

    #     last_update = current_time
