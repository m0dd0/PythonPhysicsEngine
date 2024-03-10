from typing import List
import abc

from ppe.bodies import Body


class NarrowPhase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, collision_candidates: List["Collision"]) -> List["Collision"]:
        raise NotImplementedError


class SAT(NarrowPhase):
    def __call__(self, bodies: List[Body]) -> List["Collision"]:
        # TODO
        raise NotImplementedError


# def _sat(obj1: "GameObject", obj2: "GameObject", axes: Iterable[Vector]) -> Collision:
#     min_depth = float("inf")
#     min_depth_collision = None

#     for axis in axes:
#         min1, max1 = obj1.projected_extends(axis)
#         min2, max2 = obj2.projected_extends(axis)

#         if max1 < min2 or max2 < min1:
#             return None

#         depth = min(max1, max2) - max(min1, min2)
#         if depth < min_depth:
#             min_depth = depth
#             min_depth_collision = Collision(obj1, obj2, axis, depth, None, None)

#     # in case we have multiple normals lying on the same line (e.g. rectangle) we need to make sure that the normal
#     # points to the second object so that the objects can be separated correctly
#     direction = min_depth_collision.bodyB.pos - min_depth_collision.bodyA.pos
#     if direction.dot(min_depth_collision.normal) < 0:
#         min_depth_collision.normal *= -1

#     return min_depth_collision


# def ball_polygon_collision(ball: "Ball", polygon: "ConvexPolygon") -> Collision:
#     ball_axis = None
#     ball_axis_magnitude = float("inf")
#     for vertex in polygon.vertices:
#         axis = vertex - ball.pos  # from ball to vertex
#         if axis.magnitude() < ball_axis_magnitude:
#             ball_axis = axis.normalize()
#             ball_axis_magnitude = axis.magnitude()

#     axes = chain(polygon.get_normals(), [ball_axis])

#     collision = _sat(ball, polygon, axes)
#     # !!! contact points are not calculated in _sat
#     # the collision returned by _sat has a normal which always points from obj1 to obj2
#     # obj1 is the ball and obj2 is the polygon
#     if collision is not None:
#         collision.contact_point_1 = ball.pos + collision.normal * (
#             ball.radius - collision.depth
#         )

#     return collision


# def polygon_polygon_collision(
#     polygon1: "ConvexPolygon", polygon2: "ConvexPolygon"
# ) -> Collision:
#     axes = chain(polygon1.get_normals(), polygon2.get_normals())
#     return _sat(polygon1, polygon2, axes)
#     # !!! contact points are not calculated in _sat


# def ball_ball_collision(ball1: "Ball", ball2: "Ball") -> Collision:
#     delta = ball2.pos - ball1.pos
#     dist = delta.magnitude()
#     if dist < ball1.radius + ball2.radius:
#         normal = delta.normalize()
#         return Collision(
#             ball1,
#             ball2,
#             normal,
#             ball1.radius + ball2.radius - dist,
#             ball1.pos + normal * ball1.radius,
#             None,
#         )

#     return None


# def get_collisions(
#     objects: List["GameObject"], ingore_fixed_object_collisions: bool = False
# ) -> List[Collision]:
#     collisions = []
#     for i, obj1 in enumerate(objects):
#         for obj2 in objects[i + 1 :]:
#             if ingore_fixed_object_collisions and obj1.fixed and obj2.fixed:
#                 continue
#             coll = obj1.collides_with(obj2)
#             if coll is not None:
#                 collisions.append(coll)

#     return collisions
