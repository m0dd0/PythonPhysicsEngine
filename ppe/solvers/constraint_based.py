from ppe.solvers.base import SolverBase
from typing import List

from ppe.collision.collision_detector import Collision
from ppe.joints import Joint


class ConstraintBasedSolver(SolverBase):
    def solve(
        self, collisions: List[Collision], joints: List[Joint], forces, dt: float
    ):
        raise NotImplementedError
