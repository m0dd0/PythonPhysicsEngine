from typing import List, Tuple
import abc

from ppe.bodies import Body


class BroadPhase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, objects: List[Body]) -> List[Tuple[Body, Body]]:
        raise NotImplementedError


class AABB(BroadPhase):
    def __call__(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        # TODO
        raise NotImplementedError
