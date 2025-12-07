"""
This module contains core classes and functions for the physics engine.
Namely, it defines a 2D vector class `Vec2` for all position, velocity, and force calculations,
as well as a `Contact` class that holds information about collisions between bodies.
"""

import math
from dataclasses import dataclass
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

    def __rmul__(self, scalar: float) -> "Vec2":
        return self * scalar

    def __truediv__(self, scalar: float) -> "Vec2":
        return Vec2(self.x / scalar, self.y / scalar)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vec2") -> float:
        """Returns the z-component of the cross product (2D cross product)."""
        return self.x * other.y - self.y * other.x

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        return math.sqrt(self.length_squared())

    def left_normal(self) -> "Vec2":
        """Returns the left normal of the vector."""
        return Vec2(-self.y, self.x).normalize()

    def right_normal(self) -> "Vec2":
        """Returns the right normal of the vector."""
        return Vec2(self.y, -self.x).normalize()

    def rotate(self, angle: float) -> "Vec2":
        """Rotates the vector by the given angle in radians."""
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        return Vec2(
            self.x * cos_angle - self.y * sin_angle,
            self.x * sin_angle + self.y * cos_angle,
        )

    def normalize(self) -> "Vec2":
        """Normalizes the vector to unit length.

        If the vector is zero length, a zero vector is returned.
        Otherwise, the vector is divided by its length to produce a unit vector.
        """
        l = self.length()
        if l == 0:
            return Vec2(0, 0)
        return self / l

    def to_tuple(self) -> Tuple[float, float]:
        """Returns the vector as a tuple."""
        return (self.x, self.y)

    def to_int_tuple(self) -> Tuple[int, int]:
        """Returns the vector as a tuple of integers."""
        return (int(self.x), int(self.y))

    def __eq__(self, other: "Vec2") -> bool:
        """Checks if two vectors are approximately equal (handles floating-point precision)."""
        if not isinstance(other, Vec2):
            return False
        return abs(self.x - other.x) < 1e-10 and abs(self.y - other.y) < 1e-10

    def __repr__(self) -> str:
        return f"Vec2({self.x:.2f}, {self.y:.2f})"

    def __neg__(self) -> "Vec2":
        """Returns the negation of the vector."""
        return Vec2(-self.x, -self.y)


@dataclass
class Contact:
    """Holds information about a collision between two bodies.

    Holds the following information:
    reference_body: The reference body (the body that gets penetrated).
    incident_body: The incident body (the body that is penetrating the reference body).
    normal: The normal of the contact. Points from reference body to incident body.
    penetration_depth: The depth of penetration.
    contact_points: The contact points. Usually one except for side-to-side collisions.
    """

    reference_body: "Body"  # reference body
    incident_body: "Body"  # incident body
    normal: Vec2  # normal is assumed to always point from reference body to incident body and has unit length
    penetration_depth: float
    contact_points: List[
        Vec2
    ]  # contact_points are assumed to be located on incident body
