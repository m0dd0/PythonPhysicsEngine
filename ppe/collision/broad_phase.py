from typing import List, Tuple

from ppe.bodies import Body
from ppe.collision.base import BroadPhase


class AABB(BroadPhase):
    def __call__(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        # TODO
        raise NotImplementedError
