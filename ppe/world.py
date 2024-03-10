from typing import List, Tuple

from ppe.collision.collision_detector import CollisionDetector
from ppe.solvers.impulse_based import ImpulseBasedSolver
from ppe.solvers.base import SolverBase
from ppe.bodies import Body
from ppe.vector import Vector
from ppe.joints import Joint
from ppe.integrators import IntegratorBase
from ppe.integrators import Euler


class World:
    def __init__(
        self,
        bodies: List[Body],
        joints=List[Joint],
        world_bbox: Tuple[Vector, Vector] = None,
        collision_detector: CollisionDetector = None,
        solver: SolverBase = None,
        integrator: IntegratorBase = None,
    ):
        self.world_bbox = world_bbox
        self.bodies = bodies
        self.joints = joints

        self.collision_detector = collision_detector or CollisionDetector()
        self.solver = solver or ImpulseBasedSolver()
        self.integrator = integrator or Euler()

    def update(self, dt: float):
        collisions = self.collision_detector.get_collisions(self.bodies)

        # TODO figure out way to treat external forces
        self.solver.solve(collisions, self.joints, [], dt)

        for body in self.bodies:
            self.integrator.integrate(body, dt)

        if self.world_bbox:
            bodies_in_world = [
                obj
                for obj in self.bodies
                if self.world_bbox[0].x < obj.pos.x < self.world_bbox[1].x
                and self.world_bbox[0].y < obj.pos.y < self.world_bbox[1].y
            ]
            self.bodies = bodies_in_world
