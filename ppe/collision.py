import math
import itertools
from typing import List

from ppe.objects import Ball, Polygon, GameObject
from ppe.vector import Vector


class Collision:
    def __init__(self, obj1, obj2, normal):
        self.obj1 = obj1
        self.obj2 = obj2
        self.normal = normal


def bounding_box_collision(obj1, obj2):
    return (
        obj1.bbox_min[0] <= obj2.bbox_max[0]
        and obj1.bbox_max[0] >= obj2.bbox_min[0]
        and obj1.bbox_min[1] <= obj2.bbox_max[1]
        and obj1.bbox_max[1] >= obj2.bbox_min[1]
    )


def ball_polygon_collision(ball, polygon):
    for i in range(len(polygon.vertices)):  # pylint: disable=consider-using-enumerate
        p1 = polygon.vertices[i]
        p2 = polygon.vertices[(i + 1) % len(polygon.vertices)]
        p0 = ball.pos
        d = (  # see https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
            abs(p2.x - p1.x) * (p1.y - p0.y) - (p1.x - p0.x) * (p2.y - p1.y)
        ) / math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
        if d < ball.radius:
            # return the normal vector of the line
            return Vector(p2.y - p1.y, p1.x - p2.x)

    return None


def polygon_polygon_collision(polygon1, polygon2):
    raise NotImplementedError()


def ball_ball_collision(ball1, ball2):
    raise NotImplementedError()


def get_collisions(objects: List[GameObject]) -> List[Collision]:
    static_objects = [obj for obj in objects if obj.fixed]
    moving_objects = [obj for obj in objects if not obj.fixed]

    pairs = itertools.product(static_objects, moving_objects) + itertools.product(
        moving_objects, moving_objects
    )

    collisions = []
    for obj1, obj2 in pairs:
        normal = None
        if isinstance(obj1, Ball) and isinstance(obj2, Ball):
            normal = ball_ball_collision(obj1, obj2)
        elif isinstance(obj1, Polygon) and isinstance(obj2, Polygon):
            normal = polygon_polygon_collision(obj1, obj2)
        elif isinstance(obj1, Ball) and isinstance(obj2, Polygon):
            normal = ball_polygon_collision(obj1, obj2)
        elif isinstance(obj1, Polygon) and isinstance(obj2, Ball):
            normal = ball_polygon_collision(obj2, obj1)
        else:
            raise NotImplementedError()  # should never happen

        if normal is not None:
            collisions.append(Collision(obj1, obj2, normal))

    return collisions
