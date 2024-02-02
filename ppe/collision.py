import math
from typing import List

from ppe.vector import Vector


class Collision:
    def __init__(self, obj1: "GameObject", obj2: "GameObject", normal: Vector):
        self.obj1 = obj1
        self.obj2 = obj2
        self.normal = normal


def bounding_box_collision(obj1: "GameObject", obj2: "GameObject") -> bool:
    bbox_1_min, bbox1_max = obj1.get_bbox_world()
    bbox_2_min, bbox2_max = obj2.get_bbox_world()
    return (
        bbox_1_min.x <= bbox2_max.x
        and bbox1_max.x >= bbox_2_min.x
        and bbox_1_min.y <= bbox2_max.y
        and bbox1_max.y >= bbox_2_min.y
    )


def ball_polygon_collision(ball: "Ball", polygon: "ConvexPolygon") -> Vector:
    for i in range(len(polygon.vertices)):  # pylint: disable=consider-using-enumerate
        p1 = polygon.vertices[i]
        p2 = polygon.vertices[(i + 1) % len(polygon.vertices)]
        p0 = ball.pos
        # see https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
        d = abs(
            (p2.x - p1.x) * (p1.y - p0.y) - (p1.x - p0.x) * (p2.y - p1.y)
        ) / math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
        if d < ball.radius:
            # return the normal vector of the line
            return Vector(p2.y - p1.y, p1.x - p2.x)

    return None


def polygon_polygon_collision(
    polygon1: "ConvexPolygon", polygon2: "ConvexPolygon"
) -> Vector:
    raise NotImplementedError()


def ball_ball_collision(ball1: "Ball", ball2: "Ball") -> Vector:
    raise NotImplementedError()


def get_collisions(objects: List["GameObject"]) -> List[Collision]:
    collisions = []
    for i, obj1 in enumerate(objects):
        for obj2 in objects[i + 1 :]:
            if normal := obj1.collides_with(obj2) is not None:
                collisions.append(Collision(obj1, obj2, normal))

    return collisions
