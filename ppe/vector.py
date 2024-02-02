import math
from typing import Tuple


class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(
            self.x + other.x,
            self.y + other.y,
        )

    def __sub__(self, other: "Vector") -> "Vector":
        return Vector(
            self.x - other.x,
            self.y - other.y,
        )

    def __mul__(self, other: float) -> "Vector":
        return Vector(
            self.x * other,
            self.y * other,
        )

    def __rmul__(self, other: float) -> "Vector":
        return self * other

    def __eq__(self, other: "Vector") -> bool:
        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"

    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self) -> "Vector":
        return self * (1 / self.magnitude())

    def dot(self, other: "Vector") -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vector") -> float:
        return self.x * other.y - self.y * other.x

    def rotate(self, angle: float) -> "Vector":
        return Vector(
            self.x * math.cos(angle) - self.y * math.sin(angle),
            self.x * math.sin(angle) + self.y * math.cos(angle),
        )

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)
