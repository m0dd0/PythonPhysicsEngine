from typing import List, Tuple
import abc

from ppe.bodies import Body


class BroadPhaseBase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        raise NotImplementedError


class AABB(BroadPhaseBase):
    def __call__(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        collision_candidates = []
        for i, body1 in enumerate(bodies):
            for body2 in bodies[i + 1 :]:
                if body1.kinematic and body2.kinematic:
                    continue
                if (
                    body1.shape.bbox[1].x < body2.shape.bbox[0].x
                    or body1.shape.bbox[0].x > body2.shape.bbox[1].x
                ):
                    continue
                if (
                    body1.shape.bbox[1].y < body2.shape.bbox[0].y
                    or body1.shape.bbox[0].y > body2.shape.bbox[1].y
                ):
                    continue
                collision_candidates.append((body1, body2))

        return collision_candidates
