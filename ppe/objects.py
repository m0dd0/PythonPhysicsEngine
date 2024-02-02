from abc import ABC, abstractmethod
from typing import Tuple, List

from ppe.vector import Vector
from ppe.collision import (
    Collision,
    bounding_box_collision,
    ball_polygon_collision,
    polygon_polygon_collision,
    ball_ball_collision,
)


class GameObject(ABC):
    def __init__(
        self,
        pos: Vector,  # in meter
        vel: Vector,  # in meter per second
        acc: Vector,  # in meter per second squared
        mass: float,  # in kilogram
        angle: float,  # in radian
        angular_vel: float,  # in radian per second
        bbox_rel: Tuple[Vector, Vector],
        fixed: bool = False,
        color: Tuple[int] = (255, 255, 255),
    ):
        self.pos = pos
        self.vel = vel
        self.acc = acc
        self.mass = mass
        self.angle = angle
        self.angular_vel = angular_vel
        self.bbox_rel = bbox_rel
        self.fixed = fixed
        self.color = color

    def get_bbox_world(self):
        return (
            self.pos + self.bbox_rel[0],  # min
            self.pos + self.bbox_rel[1],  # max
        )

    def update(self, dt: float):
        # TODO use verlet integration
        self.vel = self.vel + self.acc * dt
        self.pos = self.pos + self.vel * dt + 0.5 * self.acc * dt**2
        # TODO account for angular velocity

    def collides_with(self, other: "GameObject") -> Collision:
        if not bounding_box_collision(self, other):
            return None

        if isinstance(other, Ball) and isinstance(self, Ball):
            return ball_ball_collision(self, other)
        elif isinstance(other, Ball) and isinstance(self, ConvexPolygon):
            return ball_polygon_collision(other, self)
        elif isinstance(other, ConvexPolygon) and isinstance(self, Ball):
            return ball_polygon_collision(self, other)
        elif isinstance(other, ConvexPolygon) and isinstance(self, ConvexPolygon):
            return polygon_polygon_collision(self, other)
        else:
            raise ValueError(f"Unknown object types {type(self)} and {type(other)}")

    @abstractmethod
    def rotate(self, angle: float):
        raise NotImplementedError()


class Ball(GameObject):
    def __init__(
        self,
        pos: Vector,
        vel: Vector,
        acc: Vector,
        angle: float,
        angular_vel: float,
        mass: float,
        radius: float,
        fixed: bool = False,
        color: Tuple[int, int, int] = (255, 255, 255),
    ):
        super().__init__(
            pos,
            vel,
            acc,
            angle,
            angular_vel,
            mass,
            (Vector(-radius, -radius), Vector(radius, radius)),
            fixed=fixed,
            color=color,
        )
        self.radius = radius

    def rotate(self, angle: float):
        self.angle += angle

    def collides_with(self, other: GameObject) -> Collision:
        if not bounding_box_collision(self, other):
            return None

        if isinstance(other, Ball):
            return ball_ball_collision(self, other)
        elif isinstance(other, ConvexPolygon):
            return ball_polygon_collision(self, other)
        else:
            raise ValueError(f"Unknown object type {type(other)}")


class ConvexPolygon(GameObject):
    def __init__(
        self,
        vel: Vector,
        acc: Vector,
        angle: float,
        angular_vel: float,
        mass: Vector,
        vertices: List[Vector],
        fixed: bool = False,
        color: Tuple[int, int, int] = (255, 255, 255),
    ):
        assert ConvexPolygon._is_convex(
            vertices
        ), "Polygon must be convex and ordered clockwise"

        pos = ConvexPolygon._compute_center_of_mass(vertices)
        bbox_rel = ConvexPolygon._compute_bounding_box(vertices, rel_pos=pos)

        super().__init__(
            pos,
            vel,
            acc,
            mass,
            angle,
            angular_vel,
            bbox_rel,
            fixed=fixed,
            color=color,
        )

        self.vertices = vertices

    @staticmethod
    def _is_convex(vertices: List[Vector]):
        n = len(vertices)
        if n < 3:
            return False

        vertex_signs = []
        for i in range(n):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % n]
            p3 = vertices[(i + 2) % n]
            edge1 = p2 - p1
            edge2 = p3 - p2

            vertex_signs.append(edge1.cross(edge2) > 0)

        return all(vertex_signs) or not any(vertex_signs)

    @staticmethod
    def _compute_bounding_box(vertices: List[Vector], rel_pos: Vector = None):
        rel_pos = rel_pos or Vector(0, 0)

        xs = [v.x for v in vertices]
        ys = [v.y for v in vertices]
        return (Vector(min(xs), min(ys)) - rel_pos, Vector(max(xs), max(ys)) - rel_pos)

    @staticmethod
    def _compute_area(vertices: List[Vector]):
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        n = len(vertices)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i].cross(vertices[j])
        return area / 2

    @staticmethod
    def _compute_center_of_mass(vertices: List[Vector]):
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        n = len(vertices)
        area = ConvexPolygon._compute_area(vertices)
        cx = 0
        cy = 0
        for i in range(n):
            j = (i + 1) % n
            factor = vertices[i].cross(vertices[j])
            cx += (vertices[i].x + vertices[j].x) * factor
            cy += (vertices[i].y + vertices[j].y) * factor
        return Vector(cx, cy) / (6 * area)

    def collides_with(self, other: GameObject) -> Collision:
        if not bounding_box_collision(self, other):
            return None

        if isinstance(other, Ball):
            return ball_polygon_collision(other, self)
        elif isinstance(other, ConvexPolygon):
            return polygon_polygon_collision(self, other)
        else:
            raise ValueError(f"Unknown object type {type(other)}")

    def rotate(self, angle: float):
        for i, vertex in enumerate(self.vertices):
            self.vertices[i] = (vertex - self.pos).rotate(angle) + self.pos
        self.bbox_rel = ConvexPolygon._compute_bounding_box(
            self.vertices, rel_pos=self.pos
        )
