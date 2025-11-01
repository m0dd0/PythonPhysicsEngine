"""
This module defines the `World` class, which represents a physics simulation world.
The `World` class manages the bodies in the simulation and orchestrates the execution of
collision checking strategies, integration, and constraint solving.
All substeps are executed via injected strategies so the actual physics update can be
customized in a pluggable manner.
Bedsides euting the physics steps, the world class contains a set of methods to manage the
bodies in the simulation.
"""

from typing import List, Optional

from ppe.engine.common import Body, Joint, Vec2
from ppe.engine.solvers import AbstractSolver, SimpleIterativeImpulseSolver
from ppe.engine.collision_broad import AbstractBroadPhase, AABBBroadPhase
from ppe.engine.collision_narrow import AbstractNarrowPhase, DispatchNarrowPhase
from ppe.engine.collision_handlers import (
    CircleVsCircleHandler,
    SatPolygonHandler,
    CircleVsPolygonHandler,
)
from ppe.engine.integrators import AbstractIntegrator, SemiImplicitEulerIntegrator
from ppe.engine.force_generators import AbstractForceGenerator
from ppe.engine.debug import AbstractDebugDrawer
from ppe.utils.profiler import Profiler


class World:
    """
    The main simulation class that manages all bodies, constraints,
    and the high-level simulation loop.
    """

    def __init__(
        self,
        integrator: Optional[AbstractIntegrator] = None,
        solver: Optional[AbstractSolver] = None,
        broad_phase: Optional[AbstractBroadPhase] = None,
        narrow_phase: Optional[AbstractNarrowPhase] = None,
        bodies: Optional[List[Body]] = None,
        joints: Optional[List[Joint]] = None,
        force_generators: Optional[List[AbstractForceGenerator]] = None,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
        profiler: Optional[Profiler] = None,
    ):
        """
        Initializes the physics world by defining the initial objects, constraints and the
        strategies used to detect collisions and handle the physics update.

        Args:
            integrator (Optional[AbstractIntegrator]): The integrator to use for the simulation.
                The integrator is responsible for updating the velocities and positions of the bodies
                in the simulation based on the forces acting on them. Defaults to SemiImplicitEulerIntegrator.
            solver (Optional[AbstractSolver]): The solver to use for the simulation. The solver is
                responsible for resolving contacts and joints. Defaults to IterativeImpulseSolver.
            broad_phase (Optional[AbstractBroadPhase]): The broad phase collision detection strategy.
                Used to find potential collision pairs. Defaults to AABBBroadPhase.
            narrow_phase (Optional[AbstractNarrowPhase]): The narrow phase collision detection strategy.
                Used to generate contacts from potential pairs. Defaults to DispatchNarrowPhase.
            bodies (Optional[List[Body]]): A list of bodies to add to the world initially. Defaults to None.
            joints (Optional[List[Joint]]): A list of joints to add to the world initially. Defaults to None.
            force_generators (Optional[List[AbstractForceGenerator]]): A list of force generators to add
                to the world initially. Defaults to None.
            debug_drawer (Optional[AbstractDebugDrawer]): A debug drawer for visualizing the simulation.
                Defaults to None.
            profiler (Optional[Profiler]): A profiler for measuring performance. Defaults to None.
        """
        self.bodies: List[Body] = [] if bodies is None else bodies
        self.joints: List[Joint] = [] if joints is None else joints
        self.force_generators = [] if force_generators is None else force_generators

        # Inject the strategies
        self.integrator = (
            SemiImplicitEulerIntegrator() if integrator is None else integrator
        )
        self.solver = (
            SimpleIterativeImpulseSolver(debug_drawer=debug_drawer)
            if solver is None
            else solver
        )
        self.broad_phase = AABBBroadPhase() if broad_phase is None else broad_phase
        self.narrow_phase = (
            DispatchNarrowPhase(
                handlers={
                    ("circle", "circle"): CircleVsCircleHandler(
                        debug_drawer=debug_drawer
                    ),
                    ("circle", "polygon"): CircleVsPolygonHandler(
                        debug_drawer=debug_drawer
                    ),
                    ("polygon", "polygon"): SatPolygonHandler(
                        debug_drawer=debug_drawer
                    ),
                }
            )
            if narrow_phase is None
            else narrow_phase
        )

        self.debug_drawer = debug_drawer
        self.profiler = Profiler() if profiler is None else profiler

        if type(self.integrator) not in self.solver.COMPATIBLE_INTEGRATORS:
            raise TypeError(
                f"{type(self.solver).__name__} is not compatible with {type(self.integrator).__name__}."
            )

        # TODO add option to automatically remove bodies once they are outside a certain area

    def step(self, dt: float) -> None:
        """
        Advances the simulation by one time step.

        Args:
            dt (float): The time step duration (delta time).
        """
        ## Update world-space vertex data for all polygons before any checks
        # for body in self.bodies:
        #     if isinstance(body.shape, PolygonShape):
        #         body.shape.invalidate_step_cache()

        for force_generator in self.force_generators:
            force_generator.apply(self.bodies)

        ## Updates velocities based on accumulated forces
        with self.profiler.time("world/integrate1"):
            self.integrator.integrate_velocities(self.bodies, dt)

        ## Collision Detection
        with self.profiler.time("world/collision_broad"):
            potential_pairs = self.broad_phase.find_potential_pairs(self.bodies)
        with self.profiler.time("world/collision_narrow"):
            contacts = self.narrow_phase.generate_contacts(potential_pairs)

        ## solver adjusts velocities to resolve all contacts and joints
        with self.profiler.time("world/solver"):
            self.solver.solve(contacts, self.joints, dt)

        ## Updates positions based on the new, corrected velocities
        with self.profiler.time("world/integrate2"):
            self.integrator.integrate_positions(self.bodies, dt)

        # Reset all forces for the next frame
        for body in self.bodies:
            body.clear_forces()

    def add_body(self, body: Body) -> None:
        """
        Adds a body to the world.

        Args:
            body (Body): The Body object to add.
        """
        self.bodies.append(body)

    def remove_body(self, body: Body) -> None:
        """
        Removes a body from the world.

        Args:
            body (Body): The Body object to remove.
        """
        if body in self.bodies:
            self.bodies.remove(body)

    def add_joint(self, joint: Joint) -> None:
        """
        Adds a joint to the world.

        Args:
            joint (Joint): The Joint object to add.
        """
        self.joints.append(joint)

    def remove_joint(self, joint: Joint) -> None:
        """
        Removes a joint from the world.

        Args:
            joint (Joint): The Joint object to remove.
        """
        if joint in self.joints:
            self.joints.remove(joint)

    def add_force_generator(self, force_generator: AbstractForceGenerator) -> None:
        """
        Adds a force generator to the world.

        Args:
            force_generator (AbstractForceGenerator): The AbstractForceGenerator object to add.
        """
        self.force_generators.append(force_generator)

    def remove_force_generator(self, force_generator: AbstractForceGenerator) -> None:
        """
        Removes a force generator from the world.

        Args:
            force_generator (AbstractForceGenerator): The AbstractForceGenerator object to remove.
        """
        if force_generator in self.force_generators:
            self.force_generators.remove(force_generator)

    def get_bodies_at_point(self, point: Vec2) -> List[Body]:
        """
        Returns a list of bodies at the given world space point.

        Args:
            point (Vec2): The world space point to check.

        Returns:
            List[Body]: A list of bodies at the specified point.
        """
        # this can probably be optimized by using a spatial partitioning structure

        bodies_at_point = []
        for body in reversed(self.bodies):
            if body.is_point_inside(point):
                bodies_at_point.append(body)
        return bodies_at_point
