import math
from typing import List

from ppe.vector import Vector


class Collision:
    def __init__(
        self, obj1: "GameObject", obj2: "GameObject", normal: Vector, depth: float
    ):
        self.obj1 = obj1
        self.obj2 = obj2
        self.normal = normal  # normal ponints outwards from obj1
        self.depth = depth


def bounding_box_collision(obj1: "GameObject", obj2: "GameObject") -> bool:
    bbox_1_min, bbox1_max = obj1.get_bbox_world()
    bbox_2_min, bbox2_max = obj2.get_bbox_world()
    return (
        bbox_1_min.x <= bbox2_max.x
        and bbox1_max.x >= bbox_2_min.x
        and bbox_1_min.y <= bbox2_max.y
        and bbox1_max.y >= bbox_2_min.y
    )


def ball_polygon_collision(ball: "Ball", polygon: "ConvexPolygon") -> Collision:
    collisions = []
    for i in range(len(polygon.vertices)):  # pylint: disable=consider-using-enumerate
        p1 = polygon.vertices[i]
        p2 = polygon.vertices[(i + 1) % len(polygon.vertices)]
        p0 = ball.pos
        # see https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
        d = abs(
            (p2.x - p1.x) * (p1.y - p0.y) - (p1.x - p0.x) * (p2.y - p1.y)
        ) / math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
        if d < ball.radius:
            normal = Vector(p2.y - p1.y, p1.x - p2.x).normalize()
            collisions.append(Collision(polygon, ball, normal, ball.radius - d))

    if not collisions:
        return None

    return min(collisions, key=lambda c: c.depth)


def polygon_polygon_collision(
    polygon1: "ConvexPolygon", polygon2: "ConvexPolygon"
) -> Collision:
    raise NotImplementedError()


def ball_ball_collision(ball1: "Ball", ball2: "Ball") -> Collision:
    delta = ball2.pos - ball1.pos
    dist = delta.magnitude()
    if dist < ball1.radius + ball2.radius:
        normal = delta.normalize()
        return Collision(ball1, ball2, normal, ball1.radius + ball2.radius - dist)

    return None


def get_collisions(objects: List["GameObject"]) -> List[Collision]:
    collisions = []
    for i, obj1 in enumerate(objects):
        for obj2 in objects[i + 1 :]:
            coll = obj1.collides_with(obj2)
            if coll is not None:
                collisions.append(coll)

    return collisions


def handle_collision(collision: Collision):
    if collision.obj1.fixed and collision.obj2.fixed:
        return

    if not collision.obj1.fixed and not collision.obj2.fixed:
        collision.obj1.pos -= collision.normal * (collision.depth / 2)
        collision.obj2.pos += collision.normal * (collision.depth / 2)
    elif collision.obj1.fixed:
        collision.obj2.pos += collision.normal * collision.depth
    else:
        collision.obj1.pos -= collision.normal * collision.depth
