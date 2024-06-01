import pytest

from ppe.bodies import Body, Ball, ConvexPolygon
from ppe.collision.narrow_phase import SAT
from ppe.vector import Vector


class TestAABBCollision:
    def test_no_collision(self):
        ball1 = Body(shape=Ball(radius=1, com=Vector(0, 0)))
        ball2 = Body(shape=Ball(radius=1, com=Vector(3, 0)))

        assert SAT().ball_ball_collision(ball1, ball2) == []

    def test_collision_same_size(self):
        ball1 = Body(shape=Ball(radius=1, com=Vector(0, 0)))
        ball2 = Body(shape=Ball(radius=1, com=Vector(1.8, 0)))
        # overlap of 0.2

        collision = SAT().ball_ball_collision(ball1, ball2)
        assert len(collision) == 1

        collision = collision[0]

        assert (
            collision.bodyA == ball1
            and collision.bodyB == ball2
            and collision.normal == Vector(1, 0)
            and collision.penetrating_point == Vector(0.8, 0)
        ) or (
            collision.bodyA == ball2
            and collision.bodyB == ball1
            and collision.normal == Vector(-1, 0)
            and collision.penetrating_point == Vector(1, 0)
        )
        assert collision.depth == pytest.approx(0.2)
        assert collision.normal.magnitude() == 1

    def test_collision_different_size(self):
        ball1 = Body(shape=Ball(radius=2, com=Vector(0, 0)))
        ball2 = Body(shape=Ball(radius=1, com=Vector(2.7, 0)))
        # overlap of 0.3

        collision = SAT().ball_ball_collision(ball1, ball2)
        assert len(collision) == 1

        collision = collision[0]

        assert (
            collision.bodyA == ball1
            and collision.bodyB == ball2
            and collision.normal == Vector(1, 0)
            and collision.penetrating_point == Vector(1.7, 0)
        ) or (
            collision.bodyA == ball2
            and collision.bodyB == ball1
            and collision.normal == Vector(-1, 0)
            and collision.penetrating_point == Vector(2, 0)
        )


class TestSATBallBallCollision:
    def test_no_collision(self):
        ball1 = Body(shape=Ball(radius=1, com=Vector(0, 0)))
        ball2 = Body(shape=Ball(radius=1, com=Vector(3, 0)))

        assert SAT().ball_ball_collision(ball1, ball2) == []

    def test_collision_same_size(self):
        ball1 = Body(shape=Ball(radius=1, com=Vector(0, 0)))
        ball2 = Body(shape=Ball(radius=1, com=Vector(1.8, 0)))
        # overlap of 0.2

        collision = SAT().ball_ball_collision(ball1, ball2)
        assert len(collision) == 1

        collision = collision[0]

        assert (
            collision.bodyA == ball1
            and collision.bodyB == ball2
            and collision.normal == Vector(1, 0)
            and collision.penetrating_point == Vector(0.8, 0)
        ) or (
            collision.bodyA == ball2
            and collision.bodyB == ball1
            and collision.normal == Vector(-1, 0)
            and collision.penetrating_point == Vector(1, 0)
        )
        assert collision.depth == pytest.approx(0.2)
        assert collision.normal.magnitude() == 1

    def test_collision_different_size(self):
        ball1 = Body(shape=Ball(radius=2, com=Vector(0, 0)))
        ball2 = Body(shape=Ball(radius=1, com=Vector(2.7, 0)))
        # overlap of 0.3

        collision = SAT().ball_ball_collision(ball1, ball2)
        assert len(collision) == 1

        collision = collision[0]

        assert (
            collision.bodyA == ball1
            and collision.bodyB == ball2
            and collision.normal == Vector(1, 0)
            and collision.penetrating_point == Vector(1.7, 0)
        ) or (
            collision.bodyA == ball2
            and collision.bodyB == ball1
            and collision.normal == Vector(-1, 0)
            and collision.penetrating_point == Vector(2, 0)
        )


class TestSATBallPolygonCollision:
    def test_no_collision(self):
        # triangle with long side on x axis
        polygon = Body(shape=ConvexPolygon([Vector(0, 0), Vector(1, 1), Vector(2, 0)]))
        ball = Body(shape=Ball(radius=1, com=Vector(1, 3)))

        assert SAT().ball_polygon_collision(ball, polygon) == []

    def test_collision_on_edge(self):
        box = Body(
            shape=ConvexPolygon(
                [Vector(0, 0), Vector(1, 0), Vector(1, 1), Vector(0, 1)]
            )
        )
        circle = Body(shape=Ball(radius=0.5, com=Vector(0.5, 1.4)))
        # -> collision on top edge with an penetratio of 0.1

        collision = SAT().ball_polygon_collision(circle, box)

        assert len(collision) == 1
        collision = collision[0]

        assert collision.bodyA == box
        assert collision.bodyB == circle
        assert collision.penetrating_point == Vector(0.5, 0.9)
        assert collision.normal == Vector(
            0, 1
        )  # normal points outwards from penetrated object

    def test_collision_on_corner(self):
        # triangle with long side on x axis
        polygon = Body(shape=ConvexPolygon([Vector(0, 0), Vector(1, 1), Vector(2, 0)]))
        # overlap of 0.1 at top corner of triangle
        ball = Body(shape=Ball(radius=1, com=Vector(1, 1.9)))

        collision = SAT().ball_polygon_collision(ball, polygon)
        assert len(collision) == 1

        collision = collision[0]

        assert collision.bodyA == ball
        assert collision.bodyB == polygon
        assert collision.normal == Vector(0, -1)
        assert collision.depth == pytest.approx(0.1)
        assert collision.normal.magnitude() == 1
        assert collision.penetrating_point == Vector(1, 1)
