from typing import List, Tuple
import abc
import math

from ppe.bodies import Body, Ball, ConvexPolygon
from ppe.collision.collision_data import Collision


class NarrowPhaseBase(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self, collision_candidates: List[Tuple[Body, Body]]
    ) -> List[Collision]:
        raise NotImplementedError


class SAT(NarrowPhaseBase):
    def ball_ball_collision(self, ball1: Body, ball2: Body) -> List[Collision]:
        assert isinstance(ball1.shape, Ball) and isinstance(ball2.shape, Ball)

        delta = ball2.shape.com - ball1.shape.com  # from ball1 to ball2
        dist = delta.magnitude()

        if dist < ball1.shape.radius + ball2.shape.radius:
            normal = delta.normalize()
            penetration_depth = ball1.shape.radius + ball2.shape.radius - dist
            collision = Collision(
                bodyA=ball1,
                bodyB=ball2,
                normal=normal,
                depth=penetration_depth,
                penetrating_point=ball1.shape.com
                + (ball1.shape.radius - penetration_depth) * normal,
            )
            return [collision]

        return []

    def ball_polygon_collision(self, ball: Body, polygon: Body) -> List[Collision]:
        assert isinstance(ball.shape, Ball) and isinstance(polygon.shape, ConvexPolygon)

        # https://www.youtube.com/watch?v=vWs33LVrs74

        min_penetration_depth = float("inf")
        collision = None

        # first we analyze the normals of the polygon as potential separating axes
        for axis, normal_point_1 in zip(polygon.shape.normals, polygon.shape.vertices):
            # projection length of the points associated with the normal on the normal
            projected_normal_points = axis.dot(normal_point_1)
            projected_ball_center = axis.dot(ball.shape.com)
            penetration_depth = (
                projected_normal_points - projected_ball_center + ball.shape.radius
            )

            # there is a gap when the closest point of the ball is in front of the normal
            if penetration_depth < 0:
                return []

            # otherwise we might have a collision
            if penetration_depth < min_penetration_depth:
                collision = Collision(
                    bodyA=polygon,
                    bodyB=ball,
                    normal=axis,
                    depth=penetration_depth,
                    penetrating_point=ball.shape.com - axis * ball.shape.radius,
                )
                min_penetration_depth = penetration_depth

        # we also need to check the axis from the ball to the closest vertex of the polygon
        # this can be seen as equivalent to the normal of the edge of the polygon
        # we use the sqaured magnitude to avoid the square root computation
        ball_axis = None
        ball_axis_squared_magnitude = float("inf")
        for vertex in polygon.shape.vertices:
            axis = vertex - ball.shape.com  # from ball to vertex
            new_squared_ball_axis_magnitude = axis.squared_magnitude()
            if new_squared_ball_axis_magnitude < ball_axis_squared_magnitude:
                ball_axis = axis  # / math.sqrt(new_squared_ball_axis_magnitude)
                ball_axis_squared_magnitude = new_squared_ball_axis_magnitude

        ball_axis_magnitude = math.sqrt(ball_axis_squared_magnitude)
        # there is a collision if the ball is inside the polygon
        penetration_depth = ball.shape.radius - ball_axis_magnitude
        if penetration_depth < 0:
            return []

        if penetration_depth < min_penetration_depth:
            collision = Collision(
                bodyA=ball,
                bodyB=polygon,
                normal=ball_axis / ball_axis_magnitude,
                depth=penetration_depth,
                penetrating_point=ball.shape.com - ball_axis,
            )

        return [collision]

    def polygon_polygon_collision(
        self, polygon1: Body, polygon2: Body
    ) -> List[Collision]:
        assert isinstance(polygon1.shape, ConvexPolygon) and isinstance(
            polygon2.shape, ConvexPolygon
        )

        # collision_normal = None
        # min_penetration = float("inf")

        # for axis in polygon1.normals:
        #     min1, max1 = polygon1.projected_extends(axis)
        #     min2, max2 = polygon2.projected_extends(axis)

        #     if max1 < min2 or max2 < min1:
        #         return []
        raise NotImplementedError

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
