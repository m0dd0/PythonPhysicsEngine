from ppe.solvers.base import SolverBase
from typing import List

from ppe.collision.base import Collision
from ppe.joints import Joint


class ImpulseBasedSolver(SolverBase):
    def solve(
        self, collisions: List[Collision], joints: List[Joint], forces, dt: float
    ):
        raise NotImplementedError
