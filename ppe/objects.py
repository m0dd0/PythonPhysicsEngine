from abc import ABC, abstractmethod
from typing import Tuple

from ppe.vector import Vector


class GameObject(ABC):
    def __init__(
        self,
        pos: Vector,
        vel: Vector,
        acc: Vector,
        mass: float,
        bbox_min: Vector,
        bbox_max: Vector,
        fixed: bool = False,
        color: Tuple[int] = (255, 255, 255),
    ):
        self.pos = pos
        self.vel = vel
        self.acc = acc
        self.mass = mass
        self.bbox_min = bbox_min
        self.bbox_max = bbox_max
        self.fixed = fixed
        self.color = color

    def update(self, dt: float):
        # TODO use verlet integration
        self.vel = self.vel + self.acc * dt
        self.pos = self.pos + self.vel * dt + 0.5 * self.acc * dt**2


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
        xs, ys = zip(*vertices)
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
