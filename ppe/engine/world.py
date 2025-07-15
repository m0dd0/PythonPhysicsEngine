from typing import List, Optional

from ppe.engine.common import Body, Joint
from ppe.engine.solvers import AbstractSolver
from ppe.engine.collision_broad import AbstractBroadPhase
from ppe.engine.collision_narrow import AbstractNarrowPhase
from ppe.engine.integrators import AbstractIntegrator
from ppe.engine.force_generators import AbstractForceGenerator
from ppe.engine.debug import AbstractDebugDrawer


class World:
    """
    The main simulation class that manages all bodies, constraints,
    and the high-level simulation loop.
    """

    def __init__(
        self,
        integrator: AbstractIntegrator,
        solver: AbstractSolver,
        broad_phase: AbstractBroadPhase,
        narrow_phase: AbstractNarrowPhase,
        bodies: List[Body] = None,
        joints: List[Joint] = None,
        force_generators: List[AbstractForceGenerator] = None,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the physics world.

        Args:
            integrator: The integration strategy to use for updating motion.
            solver: The solver strategy to use for resolving constraints.
            broad_phase: The broad-phase collision detection strategy.
            narrow_phase: The narrow-phase collision detection strategy.
        """
        if type(integrator) not in solver.COMPATIBLE_INTEGRATORS:
            raise TypeError(
                f"{type(solver).__name__} is not compatible with {type(integrator).__name__}."
            )

        self.bodies: List[Body] = [] if bodies is None else bodies
        self.joints: List[Joint] = [] if joints is None else joints
        self.force_generators = [] if force_generators is None else force_generators

        # Inject the strategies
        self.integrator = integrator
        self.solver = solver
        self.broad_phase = broad_phase
        self.narrow_phase = narrow_phase

        # Use the property setter to initialize the drawer
        self._debug_drawer = debug_drawer

        # TODO add option to automatically remove bodies once they are outside a certain area

    @property
    def debug_drawer(self) -> Optional[AbstractDebugDrawer]:
        """
        Returns the debug drawer for visualizing the world.
        """
        return self._debug_drawer
    
    @debug_drawer.setter
    def debug_drawer(self, drawer: Optional[AbstractDebugDrawer]):
        """
        Sets the debug drawer and propagates it to all relevant subsystems.
        """
        self._debug_drawer = drawer
        
        # Pass the drawer down to the subsystems that use it
        self.broad_phase.debug_drawer = drawer
        self.narrow_phase.debug_drawer = drawer
        self.solver.debug_drawer = drawer

    def step(self, dt: float) -> None:
        """
        Advances the simulation by one time step.

        Args:
            dt: The time step duration (delta time).
        """
        ## Update world-space vertex data for all polygons before any checks
        # for body in self.bodies:
        #     if isinstance(body.shape, PolygonShape):
        #         body.shape.invalidate_step_cache()

        for force_generator in self.force_generators:
            force_generator.apply(self.bodies)

        ## Updates velocities based on accumulated forces
        self.integrator.integrate_velocities(self.bodies, dt)

        ## Collision Detection
        potential_pairs = self.broad_phase.find_potential_pairs(self.bodies)
        contacts = self.narrow_phase.generate_contacts(potential_pairs)

        ## solver adjusts velocities to resolve all contacts and joints
        self.solver.solve(contacts, self.joints, dt)

        ## Updates positions based on the new, corrected velocities
        self.integrator.integrate_positions(self.bodies, dt)

        # Reset all forces for the next frame
        for body in self.bodies:
            body.clear_forces()

    def add_body(self, body: Body) -> None:
        """
        Adds a body to the world.

        Args:
            body: The Body object to add.
        """
        self.bodies.append(body)

    def remove_body(self, body: Body) -> None:
        """
        Removes a body from the world.

        Args:
            body: The Body object to remove.
        """
        if body in self.bodies:
            self.bodies.remove(body)

    def add_joint(self, joint: Joint) -> None:
        """
        Adds a joint to the world.

        Args:
            joint: The Joint object to add.
        """
        self.joints.append(joint)

    def remove_joint(self, joint: Joint) -> None:
        """
        Removes a joint from the world.

        Args:
            joint: The Joint object to remove.
        """
        if joint in self.joints:
            self.joints.remove(joint)

    def add_force_generator(self, force_generator: AbstractForceGenerator) -> None:
        """
        Adds a force generator to the world.

        Args:
            force_generator: The AbstractForceGenerator object to add.
        """
        self.force_generators.append(force_generator)

    def remove_force_generator(self, force_generator: AbstractForceGenerator) -> None:
        """
        Removes a force generator from the world.

        Args:
            force_generator: The AbstractForceGenerator object to remove.
        """
        if force_generator in self.force_generators:
            self.force_generators.remove(force_generator)