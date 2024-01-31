import pygame
import random
import math
from abc import ABC, abstractmethod
import itertools


def draw(self, screen):
    pygame.draw.polygon(screen, self.color, self.vertices)


def bounding_box_collision(obj1, obj2):
    return (
        obj1.bbox_min[0] <= obj2.bbox_max[0]
        and obj1.bbox_max[0] >= obj2.bbox_min[0]
        and obj1.bbox_min[1] <= obj2.bbox_max[1]
        and obj1.bbox_max[1] >= obj2.bbox_min[1]
    )


def ball_polygon_collision(ball, polygon):
    if not bounding_box_collision(ball, polygon):
        return None

    for i in range(len(polygon.vertices)):  # pylint: disable=consider-using-enumerate
        p1 = polygon.vertices[i]
        p2 = polygon.vertices[(i + 1) % len(polygon.vertices)]
        d = (  # see https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
            abs(p2[0] - p1[0]) * (p1[1] - ball.x[1])
            - (p1[0] - ball.x[0]) * (p2[1] - p1[1])
        ) / math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
        if d < ball.radius:
            # return the normal vector of the line
            return (p2[1] - p1[1], p1[0] - p2[0])

    return None


class Collision:
    def __init__(self, obj1, obj2, normal):
        self.obj1 = obj1
        self.obj2 = obj2
        self.normal = normal


def polygon_polygon_collision(polygon1, polygon2):
    raise NotImplementedError()


def ball_ball_collision(ball1, ball2):
    raise NotImplementedError()


def get_collisions(static_objects, moving_objects):
    collisions = []
    pairs = itertools.product(static_objects, moving_objects) + itertools.product(
        moving_objects, moving_objects
    )

    for obj1, obj2 in pairs:
        normal = None
        if isinstance(obj1, Ball) and isinstance(obj2, Ball):
            normal = ball_ball_collision(obj1, obj2)
        elif isinstance(obj1, Ball) and isinstance(obj2, Polygon):
            normal = ball_polygon_collision(obj1, obj2)
        elif isinstance(obj1, Polygon) and isinstance(obj2, Ball):
            normal = ball_polygon_collision(obj2, obj1)
        elif isinstance(obj1, Polygon) and isinstance(obj2, Polygon):
            normal = polygon_polygon_collision(obj1, obj2)
        else:
            raise NotImplementedError()  # should never happen

        if normal is not None:
            collisions.append(Collision(obj1, obj2, normal))


def main():
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60

    BACKGROUND_COLOR = pygame.Color("white")

    GRAVITY = (0, 300)  # pixel per second^2

    BALL_RADIUS = 20
    BALL_COLOR = pygame.Color("red")
    BALL_INITIAL_POSITION = (SCREEN_WIDTH // 2, 0)
    BALL_INITAL_VELOCITY = (0, 0)  # pixel per second
    BALL_MASS = 1

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    clock = pygame.time.Clock()

    ball = Ball(
        BALL_INITIAL_POSITION,
        BALL_INITAL_VELOCITY,
        GRAVITY,
        BALL_COLOR,
        BALL_MASS,
        BALL_RADIUS,
    )
    floor = Polygon(
        (0, 0),
        (0, 0),
        (0, 0),
        pygame.Color("black"),
        math.inf,
        [
            (0, SCREEN_HEIGHT),
            (0, SCREEN_HEIGHT - 20),
            (SCREEN_WIDTH, SCREEN_HEIGHT - 20),
            (SCREEN_WIDTH, SCREEN_HEIGHT),
        ],
    )

    objects = [ball, floor]
    moving_objects = [ball]
    static_objects = [floor]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BACKGROUND_COLOR)

        collisions = get_collisions(static_objects, moving_objects)
        for collision in collisions:
            # TODO handle collison: update velocities
            pass

        for obj in objects:
            obj.update(1 / FPS)
            obj.draw(screen)

        pygame.display.flip()

        clock.tick(FPS)

    # Quit the game
    pygame.quit()


if __name__ == "__main__":
    main()
