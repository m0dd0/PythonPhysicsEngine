import abc
from typing import Tuple, List, Dict, Any
import random
import math

from ppe.vector import Vector


class Shape(abc.ABC):
    def __init__(self, vertices: List[Vector]):
        self._vertices = vertices

        self._com = self._compute_com()
        self._area = self._compute_area()

        self._bbox = None

    @property
    def vertices(self):
        return self._vertices

    @property
    def com(self):
        return self._com

    @property
    def area(self):
        return self._area

    @property
    def bbox(self):
        if self._bbox is None:
            self._bbox = self._compute_bbox()
        return self._bbox

    @abc.abstractmethod
    def _compute_com(self) -> Vector:
        raise NotImplementedError

    @abc.abstractmethod
    def _compute_area(self) -> float:
        raise NotImplementedError

    @abc.abstractmethod
    def _compute_bbox(self) -> Tuple[Vector, Vector]:
        raise NotImplementedError

    def rotate(self, angle: float):
        # updates the vertices and sets the bbox to None
        rotated_vertices = []
        for vertex in self._vertices:
            # there might be a tiny bit more efficient way to do this by using numpy or keeping the relative position of the vertices
            vertex_rel = vertex - self._com
            vertex_rotated = self._com + vertex_rel.rotate(angle)
            rotated_vertices.append(vertex_rotated)
        self._vertices = rotated_vertices

    def translate(self, delta: Vector):
        # updates the vertices, com and sets the bbox to None
        # there might be a tiny bit more efficient way to do this by using numpy
        self._vertices = [v + delta for v in self._vertices]
        self._com += delta
        self._bbox = None


class Ball(Shape):
    def __init__(self, pos: Vector, radius: float):
        self._radius = radius
        super().__init__([pos - Vector(radius, 0), pos + Vector(radius, 0)])

    @classmethod
    def create_random(
        cls,
        pos_bounds: Tuple[Vector, Vector],
        radius_bounds: Tuple[float, float],
    ) -> "Ball":
        radius = random.uniform(*radius_bounds)
        pos = Vector(
            random.uniform(pos_bounds[0].x, pos_bounds[1].x),
            random.uniform(pos_bounds[0].y, pos_bounds[1].y),
        )
        return cls(pos, radius)

    @property
    def radius(self):
        return self._radius

    def _compute_bbox(self):
        return (
            self.com - Vector(self._radius, self._radius),
            self.com + Vector(self._radius, self._radius),
        )

    def _compute_com(self):
        return self.vertices[0] + Vector(self._radius, 0)

    def _compute_area(self):
        return math.pi * self._radius**2


class ConvexPolygon(Shape):
    @staticmethod
    def vertices_are_convex(vertices: List[Vector]) -> bool:
        n = len(vertices)
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
    def vertices_are_anticlockwise(vertices: List[Vector]) -> bool:
        n = len(vertices)
        total = 0
        for i in range(n):
            j = (i + 1) % n
            total += (vertices[j].x - vertices[i].x) * (vertices[j].y + vertices[i].y)
        return total < 0

    def __init__(self, vertices: List[Vector]):
        assert len(vertices) >= 3

        if not ConvexPolygon.vertices_are_convex(vertices):
            raise ValueError("Polygon is not convex")

        if not ConvexPolygon.vertices_are_anticlockwise(vertices):
            vertices = list(reversed(vertices))

        super().__init__(vertices)

    @classmethod
    def create_rectangle(
        cls,
        pos: Vector,
        width: float,
        height: float,
        angle: float = 0,
    ) -> "ConvexPolygon":
        vertices = [
            Vector(-width / 2, -height / 2) + pos,
            Vector(-width / 2, height / 2) + pos,
            Vector(width / 2, height / 2) + pos,
            Vector(width / 2, -height / 2) + pos,
        ]
        polygon = cls(vertices)
        polygon.rotate(angle)

        return polygon

    @classmethod
    def create_random(
        cls,
        pos_bounds: Tuple[Vector, Vector],
        extend_bounds: Tuple[float, float],
        n_vertices_bounds: Tuple[int, int],
    ) -> "ConvexPolygon":
        n_vertices = random.randint(*n_vertices_bounds)

        # the extends of the ellipse
        ellpise_a = random.uniform(*extend_bounds) / 2
        ellipse_b = random.uniform(*extend_bounds) / 2

        # distribute the vertices first uniformly on the ellipse and then add a small random perturbation
        # the pertubation is limited to half the distance between two vertices
        delta_t = 2 * math.pi / n_vertices
        ts = [i * delta_t for i in range(n_vertices)]
        max_offset = delta_t / 2
        ts = [t + random.uniform(-max_offset, max_offset) for t in ts]

        vertices = [
            Vector(ellpise_a * math.cos(t), ellipse_b * math.sin(t)) for t in ts
        ]

        pos = Vector(
            random.uniform(pos_bounds[0].x, pos_bounds[1].x),
            random.uniform(pos_bounds[0].y, pos_bounds[1].y),
        )
        vertices = [v + pos for v in vertices]

        polygon = cls(vertices)

        # rotate the polygon randomly for extra randomness
        angle = random.uniform(0, 2 * math.pi)
        polygon.rotate(angle)

        return polygon

    def _compute_bbox(self) -> Tuple[Vector]:
        xs = [v.x for v in self._vertices]
        ys = [v.y for v in self._vertices]
        return (Vector(min(xs), min(ys)), Vector(max(xs), max(ys)))

    def _compute_com(self) -> Vector:
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        n = len(self._vertices)
        cx = 0
        cy = 0
        area = 0
        for i in range(n):
            j = (i + 1) % n
            factor = self._vertices[i].cross(self._vertices[j])
            cx += (self._vertices[i].x + self._vertices[j].x) * factor
            cy += (self._vertices[i].y + self._vertices[j].y) * factor
            area += factor
        return Vector(cx, cy) / (3 * area)

    def _compute_area(self) -> float:
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        n = len(self._vertices)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += self._vertices[i].cross(self._vertices[j])
        area = area / 2

        return area


class Body:
    def __init__(
        self,
        shape: Shape,
        mass: float = 1,  # in kilogram
        vel: Vector = Vector(0, 0),  # in meter per second
        acc: Vector = Vector(0, 0),  # in meter per second squared
        angular_vel: float = 0,  # in radian per second
        angular_acc: float = 0,  # in radian per second squared
        kinematic: bool = False,
        bounciness: float = 1,
        friction_coefficient: float = 0,
        visual_attributes: Dict[Any, Any] = None,
        name: str = None,
    ):
        self.shape = shape
        self.mass = mass
        self.vel = vel
        self.angular_vel = angular_vel
        self.acc = acc
        self.angular_acc = angular_acc
        self.kinematic = kinematic
        self.bounciness = bounciness
        self.friction_coefficient = friction_coefficient
        self.visual_attributes = visual_attributes or {}
        self.name = name or str(id(self))

        # all properties can be set and get and we do not do input validation

    def __repr__(self) -> str:
        return f"Body({self.name})"
