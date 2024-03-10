from typing import List, Tuple
import abc

from ppe.bodies import Body, Ball, ConvexPolygon
from ppe.collision.collision_data import Collision


class NarrowPhaseBase(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self, collision_candidates: List[Tuple[Body, Body]]
    ) -> List[Collision]:
        raise NotImplementedError


class SAT(NarrowPhaseBase):
    def ball_ball_collision(self, ball1: Ball, ball2: Ball) -> List[Collision]:
        delta = ball2.com - ball1.com
        dist = delta.magnitude()

        if dist < ball1.radius + ball2.radius:
            normal = delta.normalize()
            return [
                Collision(
                    bodyA=ball1,
                    bodyB=ball2,
                    normal=normal,
                    depth=ball1.radius + ball2.radius - dist,
                    contact_point_1=ball1.com + normal * ball1.radius,
                )
            ]

        return []

    def ball_polygon_collision(
        self, ball: Ball, polygon: ConvexPolygon
    ) -> List[Collision]:
        # https://www.youtube.com/watch?v=vWs33LVrs74
        # ball_axis = None
        # ball_axis_magnitude = float("inf")

        # for vertex in polygon.vertices:
        #     axis = vertex - ball.com  # from ball to vertex
        #     if axis.magnitude() < ball_axis_magnitude:
        #         ball_axis = axis.normalize()
        #         ball_axis_magnitude = axis.magnitude()

        # axes = chain(polygon.get_normals(), [ball_axis])

        # collision = _sat(ball, polygon, axes)
        # # !!! contact points are not calculated in _sat
        # # the collision returned by _sat has a normal which always points from obj1 to obj2
        # # obj1 is the ball and obj2 is the polygon
        # if collision is not None:
        #     collision.contact_point_1 = ball.pos + collision.normal * (
        #         ball.radius - collision.depth
        #     )

        # return collision
        raise NotImplementedError

    def polygon_polygon_collision(
        self, polygon1: ConvexPolygon, polygon2: ConvexPolygon
    ) -> List[Collision]:
        collision_normal = None
        min_penetration = float("inf")

        for axis in polygon1.normals:
            min1, max1 = polygon1.projected_extends(axis)
            min2, max2 = polygon2.projected_extends(axis)

            if max1 < min2 or max2 < min1:
                return []

    def __call__(
        self, collision_candidates: List[Tuple[Body, Body]]
    ) -> List[Collision]:
        # https://research.ncl.ac.uk/game/mastersdegree/gametechnologies/previousinformation/physics4collisiondetection/2017%20Tutorial%204%20-%20Collision%20Detection.pdf

        collisions = []

        for body1, body2 in collision_candidates:
            if isinstance(body1.shape, Ball) and isinstance(body2.shape, Ball):
                coll = self.ball_ball_collision(body1, body2)
            elif isinstance(body1.shape, Ball) and isinstance(
                body2.shape, ConvexPolygon
            ):
                coll = self.ball_polygon_collision(body1, body2)
            elif isinstance(body1.shape, ConvexPolygon) and isinstance(
                body2.shape, Ball
            ):
                coll = self.ball_polygon_collision(body2, body1)
            elif isinstance(body1.shape, ConvexPolygon) and isinstance(
                body2.shape, ConvexPolygon
            ):
                coll = self.polygon_polygon_collision(body1, body2)
            else:
                raise ValueError(
                    f"Unsupported collision between {type(body1)} and {type(body2)}"
                )

            if coll is not None:
                collisions.extend(coll)

        return collisions


class GJK(NarrowPhaseBase):
    def __call__(
        self, collision_candidates: List[Tuple[Body, Body]]
    ) -> List[Collision]:
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
