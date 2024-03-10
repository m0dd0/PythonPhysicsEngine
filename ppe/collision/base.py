from typing import List
import dataclasses

from ppe.bodies import Body
from ppe.vector import Vector

from ppe.collision.broad_phase import BroadPhase, AABB
from ppe.collision.narrow_phase import NarrowPhase, SAT


@dataclasses.dataclass
class Collision:
    bodyA: Body
    bodyB: Body
    normal: Vector  # normal points outwards from obj1 and is normalized
    depth: float
    contact_point_1: Vector
    contact_point_2: Vector


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
