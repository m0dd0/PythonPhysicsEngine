from typing import List, Tuple
import abc

from ppe.bodies import Body


class BroadPhaseBase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        raise NotImplementedError


class AABB(BroadPhaseBase):
    def __call__(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        # TODO
        raise NotImplementedError
