from abc import ABC, abstractmethod
from typing import Tuple, List, Iterator

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
        bbox: Tuple[Vector, Vector],
        fixed: bool = False,
        color: Tuple[int] = (255, 255, 255),
        name: str = None,
    ):
        self._pos = pos
        self._vel = vel
        self._acc = acc
        self._mass = mass
        self._angle = angle
        self._angular_vel = angular_vel
        self._bbox = bbox
        self._fixed = fixed
        self._color = color
        self._name = name

    @property
    def pos(self):
        return self._pos

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

    def __repr__(self) -> str:
        return f"GameObject({self.name}, pos={self.pos}, vel={self.vel}, acc={self.acc}, mass={self.mass})"

    def update(self, dt: float):
        # TODO use verlet integration
        self.vel = self.vel + self.acc * dt
        new_pos = self.pos + self.vel * dt + 0.5 * self.acc * dt**2
        self.move_to(new_pos)
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
    def rotate_to(self, angle: float):
        raise NotImplementedError()

    def rotate_by(self, angle: float):
        self.rotate_to(self.angle + angle)

    @abstractmethod
    def move_to(self, pos: Vector):
        raise NotImplementedError()

    def move_by(self, delta: Vector):
        self.move_to(self.pos + delta)

    @abstractmethod
    def projected_extends(self, axis: Vector) -> Tuple[float, float]:
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
        name: str = None,
    ):
        super().__init__(
            pos,
            vel,
            acc,
            angle,
            angular_vel,
            mass,
            (pos - Vector(radius, radius), pos + Vector(radius, radius)),
            fixed=fixed,
            color=color,
            name=name,
        )
        self._radius = radius

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value: float):
        self._radius = value
        self._bbox = (self.pos - Vector(value, value), self.pos + Vector(value, value))

    def __repr__(self) -> str:
        return f"Ball({self.name}, pos={self.pos}"  # , vel={self.vel}, acc={self.acc}, mass={self.mass}, radius={self.radius})"

    def rotate_to(self, angle: float):
        self.angle += angle

    def move_to(self, pos: Vector):
        self.pos = pos
        self._bbox = (
            self.pos - Vector(self.radius, self.radius),
            self.pos + Vector(self.radius, self.radius),
        )

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
        vel: Vector,
        acc: Vector,
        angle: float,
        angular_vel: float,
        mass: Vector,
        vertices: List[Vector],
        fixed: bool = False,
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = None,
    ):
        ConvexPolygon._check_vertices(vertices)

        pos = ConvexPolygon._compute_center_of_mass(vertices)
        bbox_rel = ConvexPolygon._compute_bounding_box(vertices)

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
            name=name,
        )

        self._vertices = vertices

    @staticmethod
    def _check_vertices(vertices: List[Vector]):
        n = len(vertices)
        if n < 3:
            raise ValueError("Polygon must have at least 3 vertices")

        vertex_signs = []
        for i in range(n):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % n]
            p3 = vertices[(i + 2) % n]
            edge1 = p2 - p1
            edge2 = p3 - p2

            vertex_signs.append(edge1.cross(edge2) > 0)

        if not (all(vertex_signs) or not any(vertex_signs)):
            raise ValueError("Polygon must be convex")

        # ensure vertice are ordered clockwise
        if all(vertex_signs):  # vertices are ordered anti-clockwise
            vertices.reverse()

    @staticmethod
    def _compute_bounding_box(vertices: List[Vector]) -> Tuple[Vector, Vector]:
        xs = [v.x for v in vertices]
        ys = [v.y for v in vertices]
        return (Vector(min(xs), min(ys)), Vector(max(xs), max(ys)))

    @staticmethod
    def _compute_area(vertices: List[Vector]) -> float:
        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        n = len(vertices)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i].cross(vertices[j])
        return area / 2

    @staticmethod
    def _compute_center_of_mass(vertices: List[Vector]) -> Vector:
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

    @property
    def vertices(self):
        return self._vertices

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

    def rotate_to(self, angle: float):
        for i, vertex in enumerate(self._vertices):
            self._vertices[i] = (vertex - self.pos).rotate(angle) + self.pos
        self._bbox = ConvexPolygon._compute_bounding_box(self._vertices)

    def move_to(self, pos: Vector):
        delta = pos - self.pos
        for i, vertex in enumerate(self._vertices):
            self._vertices[i] = vertex + delta
        self._bbox = ConvexPolygon._compute_bounding_box(self._vertices)
        self._pos = pos

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
            normal = Vector(-edge.y, edge.x).normalize()
            yield normal
