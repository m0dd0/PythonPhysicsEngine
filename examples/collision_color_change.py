import time
import logging
import math

import pygame

from ppe.world import World
from ppe.vector import Vector
from ppe.bodies import Ball, ConvexPolygon, Body
from ppe.visualization import PyGameVisualizer


SCREEN_DIMENSIONS_WORLD = (9, 5)
SCALE = 150
BACKGROUND_COLOR = (0, 0, 0)
OBJECT_COLOR = (255, 255, 255)
COLLISION_COLOR = (255, 0, 0)
COLLISION_POINT_RECT_SIZE = 0.1

FPS = 60
STEPS_PER_FRAME = 1
MANUAL_MOVEMENT_PER_STEP = 0.03

logging.basicConfig(level=logging.INFO)


def create_bodies():
    # this function contains only the body creation code and no logic
    # therefore we do not use global variables here
    fixed_box = Body(
        shape=ConvexPolygon.create_rectangle(
            com=Vector(2, 3),
            height=1,
            width=1,
        ),
        visual_attributes={"color": (255, 255, 255)},
        name="fixed_box",
    )
    fixed_ball = Body(
        shape=Ball(pos=Vector(4, 3), radius=0.5),
        visual_attributes={"color": (255, 255, 255)},
        name="fixed_ball",
    )

    return [fixed_box, fixed_ball]


def draw_collision_point(screen, visualizer, coll):
    coll_rect_world = [
        Vector(
            coll.penetrating_point.x - COLLISION_POINT_RECT_SIZE / 2,
            coll.penetrating_point.y - COLLISION_POINT_RECT_SIZE / 2,
        ),
        Vector(
            coll.penetrating_point.x + COLLISION_POINT_RECT_SIZE / 2,
            coll.penetrating_point.y - COLLISION_POINT_RECT_SIZE / 2,
        ),
        Vector(
            coll.penetrating_point.x + COLLISION_POINT_RECT_SIZE / 2,
            coll.penetrating_point.y + COLLISION_POINT_RECT_SIZE / 2,
        ),
        Vector(
            coll.penetrating_point.x - COLLISION_POINT_RECT_SIZE / 2,
            coll.penetrating_point.y + COLLISION_POINT_RECT_SIZE / 2,
        ),
    ]

    coll_rect_pixel = [visualizer.world_2_pixel_coord(pos) for pos in coll_rect_world]

    pygame.draw.polygon(
        screen, COLLISION_COLOR, [v.to_tuple() for v in coll_rect_pixel]
    )


if __name__ == "__main__":
    screen = pygame.display.set_mode(
        (SCREEN_DIMENSIONS_WORLD[0] * SCALE, SCREEN_DIMENSIONS_WORLD[1] * SCALE)
    )
    visualizer = PyGameVisualizer(screen, scale=SCALE)

    world = World(
        bodies=create_bodies(),
        world_bbox=(Vector(0, 0), Vector(*SCREEN_DIMENSIONS_WORLD)),
    )

    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # control ball with arrow keys
        # keys = pygame.key.get_pressed()
        # if keys[pygame.K_RIGHT]:
        #     ball.pos += Vector(MANUAL_MOVEMENT_PER_STEP, 0)
        # elif keys[pygame.K_LEFT]:
        #     ball.pos += Vector(-MANUAL_MOVEMENT_PER_STEP, 0)
        # elif keys[pygame.K_UP]:
        #     ball.pos += Vector(0, MANUAL_MOVEMENT_PER_STEP)
        # elif keys[pygame.K_DOWN]:
        #     ball.pos += Vector(0, -MANUAL_MOVEMENT_PER_STEP)

        physic_step_start = time.perf_counter()
        for _ in range(STEPS_PER_FRAME):
            world.update(1 / (FPS * STEPS_PER_FRAME))
        physic_step_duration = time.perf_counter() - physic_step_start

        # rendering
        screen.fill(BACKGROUND_COLOR)
        visualizer.draw(world)
        for coll in world.collisions:
            draw_collision_point(screen, visualizer, coll)
        pygame.display.flip()

        logging.info(f"{physic_step_duration:.3f}/{1/FPS:.3f}s")

        clock.tick(FPS)
