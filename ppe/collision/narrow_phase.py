from typing import List, Tuple
import abc
import math

from ppe.bodies import Body, Ball, ConvexPolygon
from ppe.collision.collision_data import Collision


class NarrowPhaseBase(abc.ABC):
    """The NarrowPhaseBase class is an abstract class for narrow phase collision detection.
    It is used to detect collisions between pairs of bodies that are collision candidates.
    The interface is a single method __call__ which takes a list of pairs of bodies and returns a list of collisions.
    The list of collisions is either empty if there are no collisions or contains one or two collisions if there is a collision.
    """

    @abc.abstractmethod
    def __call__(
        self, collision_candidates: List[Tuple[Body, Body]]
    ) -> List[Collision]:
        raise NotImplementedError


class SAT(NarrowPhaseBase):
    """The SAT class is a narrow phase collision detection algorithm that uses the Separating Axis Theorem (SAT).
    We use different methods for different shapes to detect collisions.
    """

    def ball_ball_collision(self, ball1: Body, ball2: Body) -> List[Collision]:
        """Detects collisions between two balls by checking if the distance between their centers is less than the sum of their radii.

        Args:
            ball1 (Body): The first ball.
            ball2 (Body): The second ball.

        Returns:
            List[Collision]: A list of collisions between the balls.
                The list is either empty if there are no collisions or contains one collision if there is a collision.
        """
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
        """Detects collisions between a ball and a convex polygon by checking the normals
        of the polygon and the axis from the ball to the closest vertex of the polygon.

        Args:
            ball (Body): The ball.
            polygon (Body): The convex polygon.

        Returns:
            List[Collision]: A list of collisions between the ball and the polygon.
                The list is either empty if there are no collisions or contains one collision if there is a collision.
        """
        assert isinstance(ball.shape, Ball) and isinstance(polygon.shape, ConvexPolygon)

        # https://www.youtube.com/watch?v=vWs33LVrs74

        # we also need to add a normal between the center of the ball and the closest point on the polyong
        # this avoids that we miss a separating axis when the ball is close to the edge of a polygon
        ball_axis = None
        ball_axis_polygon_vertex = None
        ball_axis_squared_magnitude = float("inf")
        for vertex in polygon.shape.vertices:
            # from vertex to ball (to be consistent with the other axis)
            axis = ball.shape.com - vertex
            new_squared_ball_axis_magnitude = axis.squared_magnitude()
            if new_squared_ball_axis_magnitude < ball_axis_squared_magnitude:
                ball_axis = axis  # / math.sqrt(new_squared_ball_axis_magnitude)
                ball_axis_squared_magnitude = new_squared_ball_axis_magnitude
                ball_axis_polygon_vertex = vertex
        ball_axis = ball_axis.normalize()

        # combine the edge-normal-pairs for both cases
        normal_edge_pairs = list(zip(polygon.shape.normals, polygon.shape.vertices)) + [
            (ball_axis, ball_axis_polygon_vertex)
        ]

        min_penetration_depth = float("inf")
        collision = None

        for axis, polygon_vertex in normal_edge_pairs:
            projected_polygon_vertex = axis.dot(polygon_vertex)
            projected_ball_center = axis.dot(ball.shape.com)

            if projected_polygon_vertex > projected_ball_center:
                # the ball center is already behind the edge which corresponds to the normal
                # this normaly means that ball is on the other side of the polygon and the
                # collision is associated with the opposite normal
                continue

            # projected_ball_center > projected_polygon_vertex
            # minimale distanz zwischen polygon und ball = projected_ball_center - projected_polygon_vertex - radius
            # minimale distanz = -penetration
            # -> penetration = radius + projected_polygon_vertex - projected_ball_center
            penetration_depth = (
                ball.shape.radius + projected_polygon_vertex - projected_ball_center
            )

            # there is a gap when the penetration depthe is negative
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

        # ball_axis = ball_axis.normalize()
        # projected_ball_center = ball_axis.dot(ball.shape.com)
        # projected_polygon_vertex = ball_axis.dot(polygon.shape.com)
        # penetration_depth = (
        #     projected_polygon_vertex - projected_ball_center + ball.shape.radius
        # )
        # if penetration_depth < 0:
        #     return []

        # if penetration_depth < min_penetration_depth:
        #     collision = Collision(
        #         bodyA=ball,
        #         bodyB=polygon,
        #         normal=ball_axis,
        #         depth=penetration_depth,
        #         penetrating_point=ball.shape.com - ball_axis,
        #     )

        return [collision]

    def polygon_polygon_collision(
        self, polygon1: Body, polygon2: Body
    ) -> List[Collision]:
        """Detects collisions between two convex polygons by checking the normals of both polygons.

        Args:
            polygon1 (Body): The first convex polygon.
            polygon2 (Body): The second convex polygon.

        Returns:
            List[Collision]: A list of collisions between the polygons.
                The list is either empty if there are no collisions or contains one collision if there is a collision.
                If there are two penetrating points at the same depth, two collisions are created.
        """
        assert isinstance(polygon1.shape, ConvexPolygon) and isinstance(
            polygon2.shape, ConvexPolygon
        )

        min_penetration_depth = math.inf
        collisions = []

        for penetrated_polygon, penetrating_polygon in [
            (polygon1, polygon2),
            (polygon2, polygon1),
        ]:
            for axis, normal_vertex in zip(
                penetrated_polygon.shape.normals, penetrated_polygon.shape.vertices
            ):
                normal_vertex_projected = axis.dot(normal_vertex)
                min_projected, max_projected = math.inf, -math.inf
                potential_penetrating_points = []

                # we project all vertices of the other polygon on the axis and look for the
                # minimum and maximum projected values. For the minimum we also store the vertex
                for vertex in penetrating_polygon.shape.vertices:
                    projected_vertex = axis.dot(vertex)
                    if min_projected > projected_vertex:
                        min_projected = projected_vertex
                        potential_penetrating_points = [vertex]
                    elif min_projected == projected_vertex:
                        potential_penetrating_points.append(vertex)
                    if max_projected < projected_vertex:
                        max_projected = projected_vertex

                if (
                    min_projected > normal_vertex_projected
                    and max_projected > normal_vertex_projected
                ):
                    # we found a separating axis
                    return []
                elif min_projected < normal_vertex_projected < max_projected:
                    penetration_depth = abs(normal_vertex_projected) - abs(
                        min_projected
                    )
                    if penetration_depth <= min_penetration_depth:
                        min_penetration_depth = penetration_depth
                        collision = Collision(
                            bodyA=penetrated_polygon,
                            bodyB=penetrating_polygon,
                            normal=axis,
                            depth=penetration_depth,
                            penetrating_point=potential_penetrating_points[0],
                        )
                        collisions.append(collision)

        return collisions

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
