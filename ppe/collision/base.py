from typing import List, Tuple
import dataclasses
import abc

from ppe.bodies import Body
from ppe.vector import Vector
from ppe.collision.broad_phase import AABB
from ppe.collision.narrow_phase import SAT


@dataclasses.dataclass
class Collision:
    bodyA: Body
    bodyB: Body
    normal: Vector  # normal points outwards from obj1 and is normalized
    depth: float
    contact_point_1: Vector
    contact_point_2: Vector


class BroadPhase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, objects: List["Body"]) -> List[Tuple[Body, Body]]:
        raise NotImplementedError


class NarrowPhase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, collision_candidates: List[Collision]) -> List[Collision]:
        raise NotImplementedError


class CollisionDetector:
    def __init__(
        self, broad_phase: BroadPhase = None, narrow_phase: NarrowPhase = None
    ):
        self.broad_phase = broad_phase or AABB()
        self.narrow_phase = narrow_phase or SAT()

    def get_collisions(self, objects: List[Body]) -> List[Collision]:
        collision_candidates = self.broad_phase(objects)
        collisions = self.narrow_phase(collision_candidates)

        return collisions
