from abc import ABC, abstractmethod
from typing import Tuple, List, Iterator
import random
import math

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
        fixed: bool,
        color: Tuple[int],
        name: str,
    ):
        self._pos = pos
        self._vel = vel
        self._acc = acc
        self._mass = mass
        self._angle = angle
        self._angular_vel = angular_vel
        self._fixed = fixed
        self._color = color
        self._name = name

        self._bbox = None
        self._update_bbox()

        self._area = None
        self._update_area()

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: Vector):
        self._pos = value
        self._update_bbox()

    @property
    def vel(self):
        return self._vel

    @vel.setter
    def vel(self, value: Vector):
        self._vel = value

    @property
    def acc(self):
        return self._acc

    @acc.setter
    def acc(self, value: Vector):
        self._acc = value

    @property
    def mass(self):
        return self._mass

    @mass.setter
    def mass(self, value: float):
        self._mass = value

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value: float):
        self._angle = value
        self._update_bbox()

    @property
    def angular_vel(self):
        return self._angular_vel

    @angular_vel.setter
    def angular_vel(self, value: float):
        self._angular_vel = value

    @property
    def bbox(self):
        return self._bbox

    @property
    def fixed(self):
        return self._fixed

    @fixed.setter
    def fixed(self, value: bool):
        self._fixed = value

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value: Tuple[int]):
        self._color = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def area(self):
        return self._area

    def __repr__(self) -> str:
        return f"GameObject({self.name}, pos={self.pos}, vel={self.vel}, acc={self.acc}, mass={self.mass})"

    def update(self, dt: float):
        # we do NOT use verlet integration as we want to be able to set the velocity directly
        # while this does not represent a real world physics, it is useful for the game
        self.vel = self.vel + self.acc * dt
        self.pos = self.pos + self.vel * dt

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
    def _update_bbox(self):
        raise NotImplementedError()

    @abstractmethod
    def _update_area(self):
        raise NotImplementedError()

    @abstractmethod
    def projected_extends(self, axis: Vector) -> Tuple[float, float]:
        raise NotImplementedError()


class Ball(GameObject):
    def __init__(
        self,
        pos: Vector,
        radius: float,
        vel: Vector = Vector(0, 0),
        acc: Vector = Vector(0, 0),
        angle: float = 0,
        angular_vel: float = 0,
        mass: float = 1,
        fixed: bool = False,
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = None,
    ):
        super().__init__(
            pos,
            vel,
            acc,
            mass,
            angle,
            angular_vel,
            fixed=fixed,
            color=color,
            name=name,
        )
        self._radius = radius

    @classmethod
    def create_random(
        cls,
        pos_bounds: Tuple[Vector, Vector],
        radius_bounds: Tuple[float, float],
        mass_bounds: Tuple[float, float],
    ) -> "Ball":
        radius = random.uniform(*radius_bounds)
        mass = random.uniform(*mass_bounds)
        pos = Vector(
            random.uniform(pos_bounds[0].x, pos_bounds[1].x),
            random.uniform(pos_bounds[0].y, pos_bounds[1].y),
        )
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        return Ball(pos, Vector(0, 0), Vector(0, 0), 0, 0, mass, radius, color=color)

    @property
    def radius(self):
        return self._radius

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value: float):
        self._angle = value
        # avoid updating the bounding box as it does not change when rotating a ball

    def __repr__(self) -> str:
        return f"Ball({self.name}, pos={self.pos}"  # , vel={self.vel}, acc={self.acc}, mass={self.mass}, radius={self.radius})"

    def _update_bbox(self):
        self._bbox = (
            self.pos - Vector(self.radius, self.radius),
            self.pos + Vector(self.radius, self.radius),
        )

    def _update_area(self):
        self._area = math.pi * self._radius**2

    def collides_with(self, other: GameObject) -> Collision:
        if not bounding_box_collision(self, other):
            return None

        if isinstance(other, Ball):
            return ball_ball_collision(self, other)
        elif isinstance(other, ConvexPolygon):
            return ball_polygon_collision(self, other)
        else:
            raise ValueError(f"Unknown object type {type(other)}")

    def projected_extends(self, axis: Vector) -> Tuple[float, float]:
        # https://en.wikipedia.org/wiki/Vector_projection#Vector_projection_2
        center = self.pos
        proj_dist = center.dot(axis) / axis.magnitude()
        return proj_dist - self._radius, proj_dist + self._radius


class ConvexPolygon(GameObject):
    def __init__(
        self,
        vertices: List[Vector],
        vel: Vector = Vector(0, 0),
        acc: Vector = Vector(0, 0),
        mass: float = 1,
        angular_vel: float = 0,
        fixed: bool = False,
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = None,
    ):
        assert len(vertices) >= 3

        self._vertices = vertices
        if not self._is_convex():
            raise ValueError("Polygon is not convex")

        if not self._is_anticlockwise():
            self._vertices = list(reversed(self._vertices))

        pos = self._compute_center_of_mass()

        super().__init__(
            pos,
            vel,
            acc,
            mass,
            0,
            angular_vel,
            fixed=fixed,
            color=color,
            name=name,
        )

    @property
    def vertices(self):
        return self._vertices

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: Vector):
        delta = value - self.pos
        for i, vertex in enumerate(self._vertices):
            self._vertices[i] = vertex + delta

        self._pos = value
        self._update_bbox()

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value: float):
        value %= 2 * math.pi
        for i, vertex in enumerate(self._vertices):
            self._vertices[i] = (vertex - self.pos).rotate(value) + self.pos

        self._angle = value
        self._update_bbox()

    @classmethod
    def create_rectangle(
        cls, pos: Vector, width: float, height: float
    ) -> "ConvexPolygon":
        half_width = width / 2
        half_height = height / 2

        polygon = ConvexPolygon(
            [
                Vector(-half_width, -half_height) + pos,
                Vector(-half_width, half_height) + pos,
                Vector(half_width, half_height) + pos,
                Vector(half_width, -half_height) + pos,
            ],
        )

        return polygon

    @classmethod
    def create_random(
        cls,
        pos_bounds: Tuple[Vector, Vector],
        extend_bounds: Tuple[float, float],
        n_vertices_bounds: Tuple[int, int],
    ) -> "ConvexPolygon":
        n_vertices = random.randint(*n_vertices_bounds)

        ellpise_a = random.uniform(*extend_bounds) / 2
        ellipse_b = random.uniform(*extend_bounds) / 2

        # distribute the vertices uniformly on the ellipse
        delta_t = 2 * math.pi / n_vertices
        ts = [i * delta_t for i in range(n_vertices)]
        # add a small random perturbation to the vertices to make the polygon more interesting
        # this effectively controls how "irregular" the polygon is
        max_offset = delta_t / 2
        ts = [t + random.uniform(-max_offset, max_offset) for t in ts]

        vertices = [
            Vector(ellpise_a * math.cos(t), ellipse_b * math.sin(t)) for t in ts
        ]

        polygon = ConvexPolygon(vertices)

        # rotate the polygon randomly for extra randomness
        polygon.angle = random.uniform(0, 2 * math.pi)

        polygon.pos = Vector(
            random.uniform(pos_bounds[0].x, pos_bounds[1].x),
            random.uniform(pos_bounds[0].y, pos_bounds[1].y),
        )

        return polygon

    def _is_convex(self) -> bool:
        n = len(self._vertices)
        vertex_signs = []
        for i in range(n):
            p1 = self._vertices[i]
            p2 = self._vertices[(i + 1) % n]
            p3 = self._vertices[(i + 2) % n]
            edge1 = p2 - p1
            edge2 = p3 - p2

            vertex_signs.append(edge1.cross(edge2) > 0)

        return all(vertex_signs) or not any(vertex_signs)

    def _is_anticlockwise(self) -> bool:
        n = len(self._vertices)
        total = 0
        for i in range(n):
            j = (i + 1) % n
            total += (self._vertices[j].x - self._vertices[i].x) * (
                self._vertices[j].y + self._vertices[i].y
            )
        return total < 0

    def _update_bbox(self) -> Tuple[Vector, Vector]:
        xs = [v.x for v in self._vertices]
        ys = [v.y for v in self._vertices]
        return (Vector(min(xs), min(ys)), Vector(max(xs), max(ys)))

    def _update_area(self) -> float:
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        n = len(self._vertices)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += self._vertices[i].cross(self._vertices[j])
        self._area = area / 2

    def _compute_center_of_mass(self) -> Vector:
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        n = len(self._vertices)
        cx = 0
        cy = 0
        # we can not use self.area as it is not yet computed when this method is called in the constructor
        area = 0
        for i in range(n):
            j = (i + 1) % n
            factor = self._vertices[i].cross(self._vertices[j])
            cx += (self._vertices[i].x + self._vertices[j].x) * factor
            cy += (self._vertices[i].y + self._vertices[j].y) * factor
            area += factor
        return Vector(cx, cy) / (3 * area)

    def __repr__(self) -> str:
        return f"ConvexPolygon({self.name}, pos={self.pos}"  # , vel={self.vel}, acc={self.acc}, mass={self.mass}, vertices={self.vertices})"

    def collides_with(self, other: GameObject) -> Collision:
        if not bounding_box_collision(self, other):
            return None

        if isinstance(other, Ball):
            return ball_polygon_collision(other, self)
        elif isinstance(other, ConvexPolygon):
            return polygon_polygon_collision(self, other)
        else:
            raise ValueError(f"Unknown object type {type(other)}")

    def projected_extends(self, axis: Vector) -> Tuple[float, float]:
        min_proj = float("inf")
        max_proj = float("-inf")
        axis_magnitude = axis.magnitude()
        for vertex in self._vertices:
            proj_dist = vertex.dot(axis) / axis_magnitude
            min_proj = min(min_proj, proj_dist)
            max_proj = max(max_proj, proj_dist)

        return min_proj, max_proj

    def get_normals(self) -> Iterator[Vector]:
        for i, p1 in enumerate(self.vertices):
            p2 = self.vertices[(i + 1) % len(self.vertices)]
            edge = p2 - p1
            normal = Vector(edge.y, -edge.x).normalize()
            yield normal
