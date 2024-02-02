from abc import ABC, abstractmethod
from typing import Tuple

from ppe.vector import Vector


class GameObject(ABC):
    def __init__(
        self,
        pos: Vector,  # in meter
        vel: Vector,  # in meter per second
        acc: Vector,  # in meter per second squared
        mass: float,  # in kilogram
        bbox_min: Vector,
        bbox_max: Vector,
        fixed: bool = False,
        color: Tuple[int] = (255, 255, 255),
    ):
        self._pos = pos
        self._vel = vel
        self._acc = acc
        self._mass = mass
        self._bbox_min = bbox_min
        self._bbox_max = bbox_max
        self._fixed = fixed
        self._color = color

    def update(self, dt: float):
        # TODO use verlet integration
        self.vel = self.vel + self.acc * dt
        self.pos = self.pos + self.vel * dt + 0.5 * self.acc * dt**2

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value


class Ball(GameObject):
    def __init__(
        self,
        pos: Vector,
        vel: Vector,
        acc: Vector,
        mass: float,
        radius: float,
        fixed: bool = False,
        color: Tuple[int] = (255, 255, 255),
    ):
        super().__init__(
            pos,
            vel,
            acc,
            mass,
            (pos.x - radius, pos.x - radius),
            (pos.x + radius, pos.x + radius),
            fixed=fixed,
            color=color,
        )
        self.radius = radius


class Polygon(GameObject):
    def __init__(
        self, pos, vel, acc, mass, vertices, fixed=False, color=(255, 255, 255)
    ):
        xs = [v.x for v in vertices]
        ys = [v.y for v in vertices]
        super().__init__(
            pos,
            vel,
            acc,
            mass,
            (min(xs), min(ys)),
            (max(xs), max(ys)),
            fixed=fixed,
            color=color,
        )
        self.vertices = vertices
