from itertools import chain
from typing import List, Tuple, Iterable
from dataclasses import dataclass

from ppe.vector import Vector


import dataclasses


@dataclasses.dataclass
class Collision:
    obj1: "GameObject"
    obj2: "GameObject"
    normal: Vector  # normal points outwards from obj1 and is normalized
    depth: float
    contact_point_1: Vector
    contact_point_2: Vector


def bounding_box_collision(obj1: "GameObject", obj2: "GameObject") -> bool:
    bbox1_min, bbox1_max = obj1.bbox
    bbox2_min, bbox2_max = obj2.bbox
    return (
        bbox1_min.x < bbox2_max.x
        and bbox1_max.x > bbox2_min.x
        and bbox1_min.y < bbox2_max.y
        and bbox1_max.y > bbox2_min.y
    )


def _sat(obj1: "GameObject", obj2: "GameObject", axes: Iterable[Vector]) -> Collision:
    min_depth = float("inf")
    min_depth_collision = None

    for axis in axes:
        min1, max1 = obj1.projected_extends(axis)
        min2, max2 = obj2.projected_extends(axis)

        if max1 < min2 or max2 < min1:
            return None

        depth = min(max1, max2) - max(min1, min2)
        if depth < min_depth:
            min_depth = depth
            min_depth_collision = Collision(obj1, obj2, axis, depth, None, None)

    # in case we have multiple normals lying on the same line (e.g. rectangle) we need to make sure that the normal
    # points to the second object so that the objects can be separated correctly
    direction = min_depth_collision.obj2.pos - min_depth_collision.obj1.pos
    if direction.dot(min_depth_collision.normal) < 0:
        min_depth_collision.normal *= -1

    return min_depth_collision


def ball_polygon_collision(ball: "Ball", polygon: "ConvexPolygon") -> Collision:
    ball_axis = None
    ball_axis_magnitude = float("inf")
    for vertex in polygon.vertices:
        axis = vertex - ball.pos  # from ball to vertex
        if axis.magnitude() < ball_axis_magnitude:
            ball_axis = axis
            ball_axis_magnitude = axis.magnitude()

    axes = chain(polygon.get_normals(), [ball_axis])

    collision = _sat(ball, polygon, axes)
    # !!! contact points are not calculated in _sat
    # the collision returned by _sat has a normal which always points from obj1 to obj2
    # obj1 is the ball and obj2 is the polygon
    if collision is not None:
        collision.contact_point_1 = ball.pos + collision.normal * (
            ball.radius - collision.depth
        )

    return collision


def polygon_polygon_collision(
    polygon1: "ConvexPolygon", polygon2: "ConvexPolygon"
) -> Collision:
    axes = chain(polygon1.get_normals(), polygon2.get_normals())
    return _sat(polygon1, polygon2, axes)
    # !!! contact points are not calculated in _sat


def ball_ball_collision(ball1: "Ball", ball2: "Ball") -> Collision:
    delta = ball2.pos - ball1.pos
    dist = delta.magnitude()
    if dist < ball1.radius + ball2.radius:
        normal = delta.normalize()
        return Collision(
            ball1,
            ball2,
            normal,
            ball1.radius + ball2.radius - dist,
            ball1.pos + normal * ball1.radius,
            None,
        )

    return None


def get_collisions(
    objects: List["GameObject"], ingore_fixed_object_collisions: bool = False
) -> List[Collision]:
    collisions = []
    for i, obj1 in enumerate(objects):
        for obj2 in objects[i + 1 :]:
            if ingore_fixed_object_collisions and obj1.fixed and obj2.fixed:
                continue
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
    # not sure if min or average of bouncieness models reality better
    e = (collision.obj1.bounciness + collision.obj2.bounciness) / 2
    impulse = (
        -(1 + e)
        * (collision.obj1.vel - collision.obj2.vel).dot(collision.normal)
        / ((1 / collision.obj1.mass) + (1 / collision.obj2.mass))
    )

    # avoid that fixed objects get a velocity value after a collision
    if not collision.obj1.fixed:
        collision.obj1.vel += impulse / collision.obj1.mass * collision.normal
    if not collision.obj2.fixed:
        collision.obj2.vel -= impulse / collision.obj2.mass * collision.normal

    collision.obj1.on_collision(collision)
    collision.obj2.on_collision(collision)


def point_in_box(point: Vector, box: Tuple[Vector, Vector]) -> bool:
    return box[0].x <= point.x <= box[1].x and box[0].y <= point.y <= box[1].y
