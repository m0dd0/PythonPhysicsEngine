import math
from typing import List, Tuple

from ppe.vector import Vector


class Collision:
    def __init__(
        self, obj1: "GameObject", obj2: "GameObject", normal: Vector, depth: float
    ):
        self.obj1 = obj1
        self.obj2 = obj2
        self.normal = normal  # normal ponints outwards from obj1 and is normalized
        self.depth = depth

    def __repr__(self) -> str:
        return f"Collision({self.obj1}, {self.obj2}, normal={self.normal}, depth={self.depth})"


def bounding_box_collision(obj1: "GameObject", obj2: "GameObject") -> bool:
    bbox1_min, bbox1_max = obj1.bbox
    bbox2_min, bbox2_max = obj2.bbox
    return (
        bbox1_min.x < bbox2_max.x
        and bbox1_max.x > bbox2_min.x
        and bbox1_min.y < bbox2_max.y
        and bbox1_max.y > bbox2_min.y
    )


def ball_polygon_collision(ball: "Ball", polygon: "ConvexPolygon") -> Collision:
    # FIXME seems like it detects collisions liek the bbox
    collisions = []
    p0 = ball.pos
    for i, p1 in enumerate(polygon.vertices):
        p2 = polygon.vertices[(i + 1) % len(polygon.vertices)]
        # see https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
        d = abs(
            (p2.x - p1.x) * (p1.y - p0.y) - (p1.x - p0.x) * (p2.y - p1.y)
        ) / math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
        if d < ball.radius:
            edge = p2 - p1
            normal = Vector(
                edge.y, -edge.x
            ).normalize()  # FIXME this is inaccurate for collsions on corner
            collisions.append(Collision(polygon, ball, normal, ball.radius - d))

    if not collisions:
        return None

    return min(collisions, key=lambda c: c.depth)


def polygon_polygon_collision(
    polygon1: "ConvexPolygon", polygon2: "ConvexPolygon"
) -> Collision:
    # SAT
    min_depth = float("inf")
    min_depth_collision = None
    for normal_poly in [polygon1, polygon2]:
        other_poly = polygon1 if normal_poly is polygon2 else polygon2

        for normal in normal_poly.get_normals():
            min1, max1 = normal_poly.projected_extends(normal)
            min2, max2 = other_poly.projected_extends(normal)

            if max1 < min2 or max2 < min1:
                return None

            depth = min(max1, max2) - max(min1, min2)
            if depth < min_depth:
                min_depth = depth
                min_depth_collision = Collision(normal_poly, other_poly, normal, depth)

    # in case we have multiple normals lying on the same line (e.g. rectangle) we need to make sure that the normal
    # points to the second object so that the objects can be separated correctly
    direction = min_depth_collision.obj2.pos - min_depth_collision.obj1.pos
    if direction.dot(min_depth_collision.normal) < 0:
        min_depth_collision.normal *= -1

    return min_depth_collision


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

    # move objects so that they don't overlap anymore
    if not collision.obj1.fixed and not collision.obj2.fixed:
        collision.obj1.pos -= collision.normal * (collision.depth / 2)
        collision.obj2.pos += collision.normal * (collision.depth / 2)
    elif collision.obj1.fixed:
        collision.obj2.pos += collision.normal * collision.depth
    else:
        collision.obj1.pos -= collision.normal * collision.depth

    # change velocities
    # https://en.wikipedia.org/wiki/Collision_response
    # https://www.chrishecker.com/images/e/e7/Gdmphys3.pdf
    e = min(collision.obj1.bounciness, collision.obj2.bounciness)
    impulse = (
        -(1 + e)
        * (collision.obj1.vel - collision.obj2.vel).dot(collision.normal)
        / ((1 / collision.obj1.mass) + (1 / collision.obj2.mass))
    )

    collision.obj1.vel += impulse / collision.obj1.mass * collision.normal
    collision.obj2.vel -= impulse / collision.obj2.mass * collision.normal

    collision.obj1.on_collision(collision)
    collision.obj2.on_collision(collision)


def point_in_box(point: Vector, box: Tuple[Vector, Vector]) -> bool:
    return box[0].x <= point.x <= box[1].x and box[0].y <= point.y <= box[1].y
