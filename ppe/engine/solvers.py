from abc import ABC, abstractmethod
from typing import List, Optional

from ppe.engine.common import Contact, Joint
from ppe.engine.integrators import SemiImplicitEulerIntegrator, PositionVerletIntegrator
from ppe.engine.debug import AbstractDebugDrawer


class AbstractSolver(ABC):
    """An abstract base class for all constraint solver strategies."""

    COMPATIBLE_INTEGRATORS = []

    def __init__(self, debug_drawer: Optional[AbstractDebugDrawer] = None) -> None:
        self.debug_drawer = debug_drawer

    @abstractmethod
    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        pass


class NoOpSolver(AbstractSolver):
    """A solver that performs no action, for debugging or simple kinematics."""

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        """Does nothing."""
        pass


class IterativeImpulseSolver(AbstractSolver):
    """
    Resolves constraints by applying impulses iteratively.
    (This is the standard solver for most physics engines).
    """

    COMPATIBLE_INTEGRATORS = [SemiImplicitEulerIntegrator]

    def __init__(
        self, iterations: int = 10, debug_drawer: Optional[AbstractDebugDrawer] = None
    ):
        super().__init__(debug_drawer)
        self.iterations = iterations

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        # TODO implement
        raise NotImplementedError("IterativeImpulseSolver is not implemented yet.")


class PositionBasedSolver(AbstractSolver):
    # This solver would declare its own compatibility
    COMPATIBLE_INTEGRATORS = [PositionVerletIntegrator]

    def __init__(
        self, iterations: int = 10, debug_drawer: Optional[AbstractDebugDrawer] = None
    ):
        super().__init__(debug_drawer)
        self.iterations = iterations

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        # TODO implement
        raise NotImplementedError("PositionBasedSolver is not implemented yet.")
