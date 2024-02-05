import math
from typing import Tuple


class Vector:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(
            self._x + other.x,
            self._y + other.y,
        )

    def __sub__(self, other: "Vector") -> "Vector":
        return Vector(
            self._x - other.x,
            self._y - other.y,
        )

    def __neg__(self) -> "Vector":
        return Vector(-self._x, -self._y)

    def __mul__(self, other: float) -> "Vector":
        return Vector(
            self._x * other,
            self._y * other,
        )

    def __rmul__(self, other: float) -> "Vector":
        return self * other

    def __truediv__(self, other: float) -> "Vector":
        return Vector(
            self._x / other,
            self._y / other,
        )

    def __eq__(self, other: "Vector") -> bool:
        return self._x == other.x and self._y == other.y

    def __repr__(self) -> str:
        return f"Vector({self._x}, {self._y})"

    def __hash__(self) -> int:
        return hash((self._x, self._y))

    def magnitude(self) -> float:
        return math.sqrt(self._x**2 + self._y**2)

    def normalize(self) -> "Vector":
        return self * (1 / self.magnitude())

    def dot(self, other: "Vector") -> float:
        return self._x * other.x + self._y * other.y

    def cross(self, other: "Vector") -> float:
        return self._x * other.y - self._y * other.x

    def rotate(self, angle: float) -> "Vector":
        return Vector(
            self._x * math.cos(angle) - self._y * math.sin(angle),
            self._x * math.sin(angle) + self._y * math.cos(angle),
        )

    def to_tuple(self) -> Tuple[float, float]:
        return (self._x, self._y)
