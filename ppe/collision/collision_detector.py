from typing import List

from ppe.bodies import Body

from ppe.collision.broad_phase import BroadPhaseBase, AABB
from ppe.collision.narrow_phase import NarrowPhaseBase, SAT
from ppe.collision.collision_data import Collision


class CollisionDetector:
    """The CollisionDetector class is responsible for detecting collisions between bodies in a physics simulation.
    It can be configured with different broad phase and narrow phase collision detection algorithms.
    """

    def __init__(
        self, broad_phase: BroadPhaseBase = None, narrow_phase: NarrowPhaseBase = None
    ):
        """Initializes the CollisionDetector with the given broad phase and narrow phase collision detection algorithms.

        Args:
            broad_phase (BroadPhaseBase, optional): The broad phase collision detection algorithm. Defaults to the AABB algorithm.
            narrow_phase (NarrowPhaseBase, optional): The narrow phase collision detection algorithm. Defaults to the SAT algorithm.
        """
        self.broad_phase = broad_phase or AABB()
        self.narrow_phase = narrow_phase or SAT()

    def get_collisions(self, objects: List[Body]) -> List[Collision]:
        """Detects collisions between the given list of bodies.

        Args:
            objects (List[Body]): A list of bodies for which to detect collisions.

        Returns:
            List[Collision]: A list of collisions between the bodies.
        """
        collision_candidates = self.broad_phase(objects)
        collisions = self.narrow_phase(collision_candidates)

        return collisions
