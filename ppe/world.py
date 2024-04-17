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
    """The World class is responsible for updating the physics simulation by integrating the bodies and solving the collisions and constraints."""

    def __init__(
        self,
        bodies: List[Body],
        joints=List[Joint],
        world_bbox: Tuple[Vector, Vector] = None,
        collision_detector: CollisionDetector = None,
        solver: SolverBase = None,
        integrator: IntegratorBase = None,
    ):
        """Initializes the World with the given bodies, joints, world bounding box, collision detector, solver and integrator.

        Args:
            bodies (List[Body]): A list of bodies in the physics simulation.
            joints (List[Joint], optional): A list of joints in the physics simulation. Defaults to [].
            world_bbox (Tuple[Vector, Vector], optional): The world bounding box. Defaults to None.
            collision_detector (CollisionDetector, optional): The collision detector. Defaults to None.
            solver (SolverBase, optional): The solver for solving collisions and constraints. Defaults to None.
            integrator (IntegratorBase, optional): The integrator for integrating the bodies. Defaults to None.
        """
        self.world_bbox = world_bbox
        self.bodies = bodies
        self.joints = joints
        self.collisions = []

        self.collision_detector = collision_detector or CollisionDetector()
        self.solver = solver or ImpulseBasedSolver()
        self.integrator = integrator or Euler()

    def update(self, dt: float):
        """Updates the physics simulation by solving the collisions and constraints and integrating the bodies.

        Args:
            dt (float): The time step for the integration. It is recommended to use a fixed time step for stability.
        """
        self.collisions = self.collision_detector.get_collisions(self.bodies)

        # TODO figure out way to treat external forces
        self.solver.solve(self.collisions, self.joints, [], dt)

        for body in self.bodies:
            self.integrator.integrate(body, dt)

        if self.world_bbox:
            bodies_in_world = [
                obj
                for obj in self.bodies
                if self.world_bbox[0].x < obj.shape.com.x < self.world_bbox[1].x
                and self.world_bbox[0].y < obj.shape.com.y < self.world_bbox[1].y
            ]
            self.bodies = bodies_in_world
