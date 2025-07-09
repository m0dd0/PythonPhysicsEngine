import math
from abc import ABC, abstractmethod
from typing import List, Tuple


class Vec2:
    """A 2D vector class for all position, velocity, and force calculations."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "Vec2":
        return Vec2(self.x / scalar, self.y / scalar)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        return math.sqrt(self.length_squared())

    def normalize(self) -> "Vec2":
        l = self.length()
        if l == 0:
            return Vec2(0, 0)
        return self / l

    def __repr__(self) -> str:
        return f"Vec2({self.x:.2f}, {self.y:.2f})"


class Body:
    """Represents a single physical object in the world."""

    def __init__(
        self,
        shape: "Shape",
        position: Vec2,
        mass: float,
        restitution: float = 0.2,
        static: bool = False,
        user_data: dict = None,
    ):
        self.shape = shape
        self.position = position
        self.angle: float = 0.0

        self.velocity: Vec2 = Vec2(0, 0)
        self.angular_velocity: float = 0.0

        self.force_accumulator: Vec2 = Vec2(0, 0)
        self.torque_accumulator: float = 0.0

        self.mass = mass
        self.restitution = restitution

        if static or mass == 0:
            self.inverse_mass: float = 0.0
            self.inverse_inertia: float = 0.0
        else:
            self.inverse_mass: float = 1.0 / mass
            self.inverse_inertia: float = (
                1.0 / self.shape.calculate_inertia(mass) if self.shape else 0.0
            )

        self.user_data = user_data

    def clear_forces(self) -> None:
        self.force_accumulator = Vec2(0, 0)
        self.torque_accumulator = 0.0

    def get_aabb(self) -> Tuple[Vec2, Vec2]:
        """
        Calculates the Axis-Aligned Bounding Box (AABB) of the body in world space.

        Returns:
            A tuple containing the min and max points of the AABB.
        """
        return self.shape.get_aabb(self.position, self.angle)


class Shape(ABC):
    """An abstract base class for all collision shapes.
    Note that a shape does NOT have any notion of rotation or translations and is always defined
    in its own coordiante system. I.e. it does not know about the position of the body it is attached to.
    Thus most of its utility methods (that are dependent on the shape) require extra information from the body it is attached to.
    """

    @abstractmethod
    def calculate_inertia(self, mass: float) -> float:
        """Calculates the moment of inertia for this shape."""
        pass

    @abstractmethod
    def get_aabb(self, position: Vec2, angle: float) -> Tuple[Vec2, Vec2]:
        """
        Calculates the world-space AABB of the shape.

        Args:
            position: The world-space position of the shape's body.
            angle: The world-space angle of the shape's body.

        Returns:
            A tuple containing the min and max points of the AABB.
        """
        pass

    # TODO check if caching of aabb and interatia improves performance and by how much. try lru cache util and custom caching implemenation where we do not need to hash the inputs


class CircleShape(Shape):
    def __init__(self, radius: float):
        self.radius = radius

    def calculate_inertia(self, mass: float) -> float:
        return 0.5 * mass * self.radius * self.radius

    def get_aabb(self, position: Vec2, angle: float) -> Tuple[Vec2, Vec2]:
        radius = self.radius
        return (
            Vec2(position.x - radius, position.y - radius),
            Vec2(position.x + radius, position.y + radius),
        )


class PolygonShape(Shape):
    def __init__(self, vertices: List[Vec2]):
        self.vertices = vertices
        # TODO check if caching rotated vertices improves performance

    def calculate_inertia(self, mass: float) -> float:
        min_x = min(v.x for v in self.vertices)
        max_x = max(v.x for v in self.vertices)
        min_y = min(v.y for v in self.vertices)
        max_y = max(v.y for v in self.vertices)
        width = max_x - min_x
        height = max_y - min_y
        return (1.0 / 12.0) * mass * (width**2 + height**2)

    def get_aabb(self, position: Vec2, angle: float) -> Tuple[Vec2, Vec2]:
        """Calculates the AABB of the polygon shape in world space."""
        rotated_vertices = [
            Vec2(
                v.x * math.cos(angle) - v.y * math.sin(angle) + position.x,
                v.x * math.sin(angle) + v.y * math.cos(angle) + position.y,
            )
            for v in self.vertices
        ]

        min_x = min(v.x for v in rotated_vertices)
        max_x = max(v.x for v in rotated_vertices)
        min_y = min(v.y for v in rotated_vertices)
        max_y = max(v.y for v in rotated_vertices)

        return Vec2(min_x, min_y), Vec2(max_x, max_y)


class CompoundShape(Shape):
    def __init__(self, sub_shapes: List[Tuple[Shape, Vec2, float]]):
        """
        Initializes a compound shape with a list of shapes.

        Args:
            sub_shapes: A list of tuples, each containing a shape, its position relative to the compound shape's origin,
                        and its rotation angle.
        """
        # TODO
        raise NotImplementedError("CompoundShape is not implemented yet.")

    def get_aabb(self, position, angle) -> Tuple[Vec2, Vec2]:
        raise NotImplementedError("CompoundShape is not implemented yet.")


class Contact:
    """Holds information about a collision between two bodies."""

    def __init__(
        self, body_a: Body, body_b: Body, normal: Vec2, penetration_depth: float
    ):
        self.body_a = body_a
        self.body_b = body_b
        self.normal = normal
        self.penetration_depth = penetration_depth


class DistanceJoint:
    """A constraint that keeps two bodies at a fixed distance."""

    def __init__(
        self,
        body_a: Body,
        body_b: Body,
        anchor_a: Vec2,
        anchor_b: Vec2,
        distance: float,
    ):
        self.body_a = body_a
        self.body_b = body_b
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        self.distance = distance
