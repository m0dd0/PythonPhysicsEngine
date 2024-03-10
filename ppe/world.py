from typing import List, Tuple

from ppe.collision.base import CollisionDetector
from ppe.solver.impulse_based import ImpulseSolver
from ppe.solver.base import Solver
from ppe.bodies import Body
from ppe.vector import Vector
from ppe.joints import Joint
from ppe.integrators import Integrator
from ppt.integrators import Euler


class World:
    def __init__(
        self,
        bodies: List[Body],
        joints=List[Joint],
        world_bbox: Tuple[Vector, Vector] = None,
        collision_detector: CollisionDetector = None,
        solver: Solver = None,
        integrator: Integrator = None,
    ):
        self.world_bbox = world_bbox
        self.bodies = bodies
        self.joints = joints

        self.collision_detector = collision_detector or CollisionDetector()
        self.solver = solver or ImpulseSolver()
        self.integrator = integrator or Euler()

    def update(self, dt: float):
        collisions = self.collision_detector.get_collisions(self.bodies)

        self.solver.solve(collisions, self.joints, [], dt)

        if self.world_bbox:
            bodies_in_world = [
                obj
                for obj in self.bodies
                if self.world_bbox[0].x < obj.pos.x < self.world_bbox[1].x
                and self.world_bbox[0].y < obj.pos.y < self.world_bbox[1].y
            ]
            self.bodies = bodies_in_world
