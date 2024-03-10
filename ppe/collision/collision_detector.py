from typing import List

from ppe.bodies import Body

from ppe.collision.broad_phase import BroadPhaseBase, AABB
from ppe.collision.narrow_phase import NarrowPhaseBase, SAT
from ppe.collision.collision_data import Collision


class CollisionDetector:
    def __init__(
        self, broad_phase: BroadPhaseBase = None, narrow_phase: NarrowPhaseBase = None
    ):
        self.broad_phase = broad_phase or AABB()
        self.narrow_phase = narrow_phase or SAT()

    def get_collisions(self, objects: List[Body]) -> List[Collision]:
        collision_candidates = self.broad_phase(objects)
        collisions = self.narrow_phase(collision_candidates)

        return collisions
