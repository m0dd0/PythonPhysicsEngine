"""
Module containing classes for solving physics constraints in a simulation.

This module defines an abstract base class for all solvers, as well as concrete implementations
for different types of solvers. The available solvers are:

- `IterativeImpulseSolver`: An iterative impulse-based solver for solving physics constraints.
- `PositionBasedSolver`: A position-based solver for solving physics constraints.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ppe.engine.common import Contact, Joint, Vec2, Body
from ppe.engine.integrators import (
    SemiImplicitEulerIntegrator,
    PositionVerletIntegrator,
    NoOpIntegrator,
)
from ppe.engine.debug import AbstractDebugDrawer


class AbstractSolver(ABC):
    """An abstract base class for all constraint solver strategies.
    A solver takes a list of contacts and a list of joints and resolves them by updating
    the bodies posision and velocity.
    Each solver must define a list of integrator classes that it is compatible with.
    """

    COMPATIBLE_INTEGRATORS = []

    def __init__(self, debug_drawer: Optional[AbstractDebugDrawer] = None) -> None:
        """
        Initializes the solver with an optional debug drawer.

        Args:
            debug_drawer (Optional[AbstractDebugDrawer]): An optional debug drawer for visualizing the simulation.
        """
        self.debug_drawer = debug_drawer

    def _compute_effective_inverse_mass(
        self, contact: Contact, contact_point: Vec2
    ) -> float:
        """
        Computes the effective inverse mass of two bodies in a contact.

        The effective inverse mass represents how resistant the two bodies are to being pushed apart AND the resistance to change their rotation.
        It is used in the impulse-based solver to compute the impulse magnitude.

        Args:
            contact (Contact): The contact for which to compute the effective inverse mass.
            contact_point (Vec2): The contact point for which to compute the effective inverse mass.

        Returns:
            float: The effective inverse mass of the two bodies in the contact.
        """
        r_ref = contact_point - contact.reference_body.position
        r_inc = contact_point - contact.incident_body.position

        inverse_effective_mass = (
            contact.reference_body.inverse_mass
            + contact.incident_body.inverse_mass
            + (
                r_ref.cross(contact.normal) ** 2
                * contact.reference_body.inverse_inertia
            )
            + (r_inc.cross(contact.normal) ** 2 * contact.incident_body.inverse_inertia)
        )

        return inverse_effective_mass

    @abstractmethod
    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        """
        Solves the given list of contacts and joints by updating the bodies' position and velocity.

        Args:
            contacts (List[Contact]): A list of contacts to solve.
            joints (List[Joint]): A list of joints to solve.
            dt (float): The time step for the solver.
        """
        pass


class NoOpSolver(AbstractSolver):
    """A solver that performs no action, for debugging or simple kinematics."""

    COMPATIBLE_INTEGRATORS = [
        NoOpIntegrator,
        SemiImplicitEulerIntegrator,
        PositionVerletIntegrator,
    ]

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        """Does nothing."""
        pass


class IterativeImpulseSolver(AbstractSolver):
    """
    A simple iterative impulse-based solver for solving collisions and constraints.
    This solver applies impulses iteratively to solve collisions and constraints.
    The impulses change the velocity of the bodies, so that the bodies position gets integrated
    to physically valid positions. Therefore, this solver is compatible with integrators
    that determine the bodies position based on their velocity like the semi-implicit euler integrator.
    """

    COMPATIBLE_INTEGRATORS = [SemiImplicitEulerIntegrator]

    def __init__(
        self,
        iterations: int = 30,
        baumgarte_stabilization_factor: float = 0.2,
        baumgarte_stabilization_threshold: float = 0.01,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the solver with the given number of iterations, Baumgarte stabilization factor and allowance,
        an optional debug drawer, and a boolean indicating whether to use a hacky positional correction.
        The solver applies impulses iteratively to solve collisions and constraints.

        Args:
            iterations (int, optional): The number of iterations to perform when solving the constraints.
                This is how often, the impulses are recomputed and applied. Especially helpful for stacking scenarios.
                Defaults to 30.
            baumgarte_stabilization_factor (float, optional): The factor for the Baumgarte stabilization.
                Can be thought of the fraction of the overlap depth that a the baumgarte impulse will correct.
                Setting this to 1 might seem intuitive but ca result in unstable behavior for complex stacking scenarios.
                Defaults to 0.2.
            baumgarte_stabilization_thershold (float, optional): The maximum penetration depth
                that is tolerated before baumgarte stabilization gets applied.
                Defaults to 0.0.
            debug_drawer (Optional[AbstractDebugDrawer], optional): An optional debug drawer for visualizing the simulation.
        """
        super().__init__(debug_drawer)
        self.iterations = iterations
        self.baumgarte_stabilization_factor = baumgarte_stabilization_factor
        self.baumgarte_stabilization_threshold = baumgarte_stabilization_threshold

    def _apply_impulse(self, body: Body, impulse: Vec2, contact_vector: Vec2):
        """Applies both linear and angular impulse to a body that updates its velocity and angular velocity.

        Args:
            body (Body): The body to apply the impulse to.
            impulse (Vec2): The impulse to apply.
            contact_vector (Vec2): The contact vector. This is needed to correctly compute
                the angular impulse.
        """
        body.velocity += impulse * body.inverse_mass
        body.angular_velocity += contact_vector.cross(impulse) * body.inverse_inertia

    def _solve_contact_point(
        self,
        contact_point: Vec2,
        contact: Contact,
        dt: float,
        effective_inverse_mass: float,
    ):
        """Applies an impulse (change in velocity) to the bodies in the contact based on
        the given contact point. For resolving a collision with multiple contact points,
        this method needs to be called with all contact points in the contact information.

        Args:
            contact_point (Vec2): The contact point for which to apply the impulse.
            contact (Contact): The contact manifold to solve.
            dt (float): The time step for the solver.
            effective_inverse_mass (float): The effective inverse mass of the bodies in the contact.
                This value remains constant for a given contact over the solver iterations.
                Therefore it is only precomputed once and passed to this method.
        """
        # compute the vectors from the bodies centers of mass to the contact point
        r_ref = contact_point - contact.reference_body.position
        r_inc = contact_point - contact.incident_body.position

        ### 1. Calculate the velocity at the contact point for each body.
        # this is the bodies velocity and angular velocity at the contact point.
        v_coll_point_ref = contact.reference_body.velocity + Vec2(
            -contact.reference_body.angular_velocity * r_ref.y,
            contact.reference_body.angular_velocity * r_ref.x,
        )
        v_coll_point_inc = contact.incident_body.velocity + Vec2(
            -contact.incident_body.angular_velocity * r_inc.y,
            contact.incident_body.angular_velocity * r_inc.x,
        )

        # relative velocity of both bodies at the contact point
        # relative_normal_velocity_factor is a scaling factor for the (unit-length) collision normal vector
        # so relative_normal_velocity_factor * contact.normal is the relative velocity in the collision normal direction
        relative_collision_point_velocity = v_coll_point_inc - v_coll_point_ref
        relative_normal_velocity_factor = relative_collision_point_velocity.dot(
            contact.normal
        )

        ### 2. Calculate the effective mass
        # the effective mass represents how resistant the two bodies are to being pushed apart AND the resistance to change their rotation
        # the derivative for the effective mass cna be found here: https://en.wikipedia.org/wiki/Collision_response
        # the effective inverse mass gets already precomputed since it remains the same over the iteratiosn
        # inverse_effective_mass = (
        #     contact.reference_body.inverse_mass
        #     + contact.incident_body.inverse_mass
        #     + (
        #         r_ref.cross(contact.normal) ** 2
        #         * contact.reference_body.inverse_inertia
        #     )
        #     + (r_inc.cross(contact.normal) ** 2 * contact.incident_body.inverse_inertia)
        # )

        if effective_inverse_mass > 0 and relative_normal_velocity_factor < 0:
            ### 3. Calculate the impulse magnitude (j)
            # e is the restitution coefficient, which can take values between 0 and 1
            # the higher it is, the more "bouncier" the objects are
            e = min(
                contact.reference_body.restitution, contact.incident_body.restitution
            )

            # j is the magnitude of the impulse that gets applied in the direction of the contact normal
            # using e=0 results in an impulse that just cancels the relative velocity
            # using e=1 results in an impulse that is equal to the relative velocity but in the opposite direction
            j = -(1.0 + e) * relative_normal_velocity_factor
            j /= effective_inverse_mass
            j /= len(
                contact.contact_points
            )  # Distribute impulse over all contact points

            ### 4. Apply the impulse
            impulse = contact.normal * j
            self._apply_impulse(contact.reference_body, -impulse, r_ref)
            self._apply_impulse(contact.incident_body, impulse, r_inc)

        ### 5. Positional Correction with Baumgarte Stabilization
        # This applies a small extra impulse to push sinking objects apart.
        position_error_to_fix = max(
            0.0, contact.penetration_depth - self.baumgarte_stabilization_threshold
        )
        correction_impulse_magnitude = (
            (self.baumgarte_stabilization_factor / dt)
            * position_error_to_fix
            / effective_inverse_mass
        )
        correction_impulse_magnitude /= len(
            contact.contact_points
        )  # Distribute impulse
        correction_impulse_magnitude /= self.iterations

        correction_impulse = contact.normal * correction_impulse_magnitude
        self._apply_impulse(contact.reference_body, -correction_impulse, r_ref)
        self._apply_impulse(contact.incident_body, correction_impulse, r_inc)

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        """
        Solves the given contacts by updating the bodies' velocity.
        The velocity is updated by iterativly applying impulses to the bodies.

        Args:
            contacts (List[Contact]): A list of contacts to solve.
            joints (List[Joint]): A list of joints to solve.
            dt (float): The time step for the solver.
        """
        if len(joints) > 0:
            raise NotImplementedError("Joint solving is not implemented yet.")

        # the effective inverse mass depends only on the bodies positions, masses and inertias
        # these values stay constant over the iterations.
        # therfore we can compute them once and store them in a list to improve performance
        inverse_effective_masses = [
            [
                self._compute_effective_inverse_mass(contact, contact_point)
                for contact_point in contact.contact_points
            ]
            for contact in contacts
        ]

        # The main loop that iterates multiple times to allow impulses to propagate
        for i_iteration in range(self.iterations):
            for i_contact, contact in enumerate(contacts):
                for i_point, contact_point in enumerate(contact.contact_points):
                    self._solve_contact_point(
                        contact_point,
                        contact,
                        dt,
                        inverse_effective_masses[i_contact][i_point],
                    )

            # Joint solving would go here in a similar loop
            # for joint in joints:
            #     self._solve_joint(joint, dt)


class SimpleIterativeImpulseSolver(AbstractSolver):
    """
    A simple iterative impulse-based solver for solving collisions and constraints.
    This solver applies impulses iteratively to solve collisions and constraints.
    It does NOT account for rotational motion to keep things as simple as possible.
    The impulses change the velocity of the bodies, so that the bodies position gets integrated
    to physically valid positions. Therefore, this solver is compatible with integrators
    that determine the bodies position based on their velocity like the semi-implicit euler integrator.
    """

    COMPATIBLE_INTEGRATORS = [SemiImplicitEulerIntegrator]

    def __init__(
        self,
        iterations: int = 30,
        baumgarte_stabilization_factor: float = 0.2,
        baumgarte_stabilization_threshold: float = 0.01,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
        teleport_positional_correction: bool = False,
    ):
        """
        Initializes the solver with the given number of iterations, Baumgarte stabilization factor and allowance,
        an optional debug drawer, and a boolean indicating whether to use a hacky positional correction.
        The solver applies impulses iteratively to solve collisions and constraints.
        Note that this solver does NOT account for rotational motion to keep things as simple as possible.

        Args:
            iterations (int, optional): The number of iterations to perform when solving the constraints.
                This is how often, the impulses are recomputed and applied. Especially helpful for stacking scenarios.
                Defaults to 30.
            baumgarte_stabilization_factor (float, optional): The factor for the Baumgarte stabilization.
                Can be thought of the fraction of the overlap depth that a the baumgarte impulse will correct.
                Setting this to 1 might seem intuitive but ca result in unstable behavior for complex stacking scenarios.
                Defaults to 0.2.
            baumgarte_stabilization_thershold (float, optional): The maximum penetration depth
                that is tolerated before baumgarte stabilization gets applied.
                Defaults to 0.0.
            debug_drawer (Optional[AbstractDebugDrawer], optional): An optional debug drawer for visualizing the simulation.
            teleport_positional_correction (bool, optional): A boolean indicating whether to use a hacky positional correction.
                In contrast to baumgarte stabilization, this method solves the overlap by manually updating the bodies position.
                This works for simple scnearios, but results in physically incorrect and unstable behavior for more complex scenarios.
                It is kept here to show the different effects of both methods.
                Defaults to False.
        """
        super().__init__(debug_drawer)
        self.baumgarte_stabilization_factor = baumgarte_stabilization_factor
        self.baumgarte_stabilization_threshold = baumgarte_stabilization_threshold
        self.iterations = iterations
        self.teleport_positional_correction = teleport_positional_correction

    def _solve_contact(self, contact: Contact, dt: float) -> None:
        """
        Solves the given contact by updating the bodies' velocity.
        The impulse that is applied is calculated based on the relative collision velocity.
        The impulse is then applied to both bodies.
        An extra baumgarte impulse is applied to push objects apart.

        Args:
            contact (Contact): The contact to solve.
            dt (float): The time step for the solver.
        """
        ### update velcoties by applying an impulse
        # https://en.wikipedia.org/wiki/Collision_response
        # https://www.chrishecker.com/images/e/e7/Gdmphys3.pdf
        relative_velocity = (
            contact.incident_body.velocity - contact.reference_body.velocity
        )
        relative_normal_velocity_factor = relative_velocity.dot(contact.normal)
        # relative_normal_velocity_factor is a scaling factor for the (unit-length) collision normal vector
        # so relative_normal_velocity_factor * contact.normal is the relative velocity in the collision normal direction

        inverse_effective_mass = (
            contact.reference_body.inverse_mass + contact.incident_body.inverse_mass
        )

        # If effective_mass is zero, both bodies are static,
        # these type of collision should've been removed in the broad phase already
        assert inverse_effective_mass != 0
        # only apply the impulse if the bodies are moving towards each other

        if relative_normal_velocity_factor < 0:
            # e is the restitution coefficient, which can take values between 0 and 1
            # the higher it is, the more "bouncier" the objects are
            e = min(
                contact.reference_body.restitution, contact.incident_body.restitution
            )

            # j is the magnitude of the impulse that gets applied in the direction of the contact normal
            # using e=0 results in an impulse that just cancels the relative velocity
            # using e=1 results in an impulse that is equal to the relative velocity but in the opposite direction
            j = -(1.0 + e) * relative_normal_velocity_factor
            j /= inverse_effective_mass

            # apply the impulse along the contact normal
            # note that for static bodies the inverse mass is zero and thus the applied velocity change is zero
            impulse = contact.normal * j

            contact.reference_body.velocity -= (
                impulse * contact.reference_body.inverse_mass
            )
            contact.incident_body.velocity += (
                impulse * contact.incident_body.inverse_mass
            )

        ### apply baumgarte stabilization
        # this is for fixing the posistional error (penetration depth) without explicitly updating the bodies position
        # instead we apply another impulse in the opposite direction of the contact normal
        # the magnitude is chosen so that the penetration depth is reduced by a factor of baumgarte_stabilization_factor in each iteration
        # note that this gets applied even if the bodies are already moving away from each other
        # by doing so we make sure that there overlap gets removed fast enough
        position_error_to_fix = max(
            0.0, contact.penetration_depth - self.baumgarte_stabilization_threshold
        )
        correction_velocity = (
            self.baumgarte_stabilization_factor / dt
        ) * position_error_to_fix
        correction_impulse_magnitude = correction_velocity / inverse_effective_mass
        correction_impulse_magnitude /= self.iterations

        contact.reference_body.velocity -= (
            contact.normal
            * correction_impulse_magnitude
            * contact.reference_body.inverse_mass
        )
        contact.incident_body.velocity += (
            contact.normal
            * correction_impulse_magnitude
            * contact.incident_body.inverse_mass
        )

        #### hacky alternative to baumgarte stabilization: move objects so that they don't overlap anymore
        # this is a hacky posistional correction and baumgarte stabilization should be preferred
        # however, it is kept here to show the different effects of both methods
        if self.teleport_positional_correction:
            if (
                contact.reference_body.inverse_mass != 0
                and contact.incident_body.inverse_mass != 0
            ):
                # put both bodies apart by moving each of them along the contact normal
                contact.reference_body.position -= (
                    contact.normal
                    * contact.penetration_depth
                    * contact.reference_body.inverse_mass
                    / inverse_effective_mass
                )

                contact.incident_body.position += (
                    contact.normal
                    * contact.penetration_depth
                    * contact.incident_body.inverse_mass
                    / inverse_effective_mass
                )

            # if one object is static, move the other the full penetration depth along the contact normal
            elif contact.reference_body.inverse_mass == 0:
                contact.incident_body.position += (
                    contact.normal * contact.penetration_depth
                )
            else:
                contact.reference_body.position -= (
                    contact.normal * contact.penetration_depth
                )

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        """
        Solves the given contacts by updating the bodies' velocity.
        The velocity is updated by iterativly applying impulses to the bodies.
        Note that this solver does NOT account for rotational motion.

        Args:
            contacts (List[Contact]): A list of contacts to solve.
            joints (List[Joint]): A list of joints to solve.
            dt (float): The time step for the solver.
        """
        if len(joints) > 0:
            raise NotImplementedError("Joint solving is not implemented yet.")

        # TODO use dynamic number of iterations
        for i in range(self.iterations):
            for contact in contacts:
                self._solve_contact(contact, dt)


class IterativePositionBasedSolver(AbstractSolver):
    """
    Resolves constraints by directly modifying object positions.
    It must be paired with a PositionVerletIntegrator.
    Note that this is only an experimental implementation. A better working version of this
    solver requires to recompute the contact in each iteration. This is however not possible
    with the current architecture.
    """

    COMPATIBLE_INTEGRATORS = [PositionVerletIntegrator]

    def __init__(
        self,
        iterations: int = 30,
        stiffness: float = 0.6,
        allowed_penetration_threshold: float = 0.01,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the position-based solver.

        Args:
            iterations (int): The number of solver iterations. Defaults to 10.
            stiffness (float): A factor (0 to 1) of how much of the error to
                correct per iteration. 1.0 can be unstable. Defaults to 0.8.
            penetration_threshold (float): A small amount of penetration to allow (prevents jitter)
                and that is ignored by the solver. This can prevent jitter. Defaults to 0.01.
            debug_drawer (AbstractDebugDrawer, optional):
        """
        super().__init__(debug_drawer)
        self.iterations = iterations
        self.stiffness = stiffness
        self.allowed_penetration_threshold = allowed_penetration_threshold

    def _solve_contact_point(
        self, contact: Contact, contact_point: Vec2, effective_inverse_mass: float
    ) -> None:
        """Calculates and applies a direct positional correction to correct position for the
        given contact.

        Args:
            contact (Contact): The contact to correct for.
            contact_point (Vec2): The contact point to correct for.
            effective_inverse_mass (float): The effective inverse mass of the bodies in
                the contact wrt the contact point.
        """
        # 1. Calculate the error to fix
        error_to_fix = max(
            0.0, contact.penetration_depth - self.allowed_penetration_threshold
        )
        if error_to_fix == 0.0:
            return

        # 2. We will apply a fraction of the correction at each contact point
        correction_per_point = (
            error_to_fix / len(contact.contact_points)
        ) * self.stiffness

        # 3. Calculate the Positional Correction Magnitude
        # This is the magnitude of the "push" needed from this contact point
        # to resolve its share of the error.
        delta_p_magnitude = (
            correction_per_point / effective_inverse_mass / self.iterations
        )
        correction_vector = contact.normal * delta_p_magnitude

        # 5. Apply the Correction Directly to Position and Angle
        # Apply linear correction (weighted by inverse mass)
        contact.reference_body.position -= (
            correction_vector * contact.reference_body.inverse_mass
        )
        contact.incident_body.position += (
            correction_vector * contact.incident_body.inverse_mass
        )

        # Apply angular correction (weighted by inverse inertia)
        r_ref = contact_point - contact.reference_body.position
        r_inc = contact_point - contact.incident_body.position
        r_ref_cross_n = r_ref.cross(contact.normal)
        r_inc_cross_n = r_inc.cross(contact.normal)

        contact.reference_body.angle -= (
            r_ref_cross_n * contact.reference_body.inverse_inertia
        ) * delta_p_magnitude
        contact.incident_body.angle += (
            r_inc_cross_n * contact.incident_body.inverse_inertia
        ) * delta_p_magnitude

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        """
        Iteratively adjusts body positions to resolve penetrations.

        Args:
            contacts (List[Contact]): A list of contacts to solve.
            joints (List[Joint]): A list of joints to solve.
            dt (float): The time step for the solver. Note that this parameter is not used
                by this solver. However, it is listed here to adhere to the abstract method signature.
        """
        if len(joints) > 0:
            raise NotImplementedError("Joint solving is not implemented yet.")

        # the effective inverse mass depends only on the bodies positions, masses and inertias
        # these values stay constant over the iterations.
        # therfore we can compute them once and store them in a list to improve performance
        inverse_effective_masses = [
            [
                self._compute_effective_inverse_mass(contact, contact_point)
                for contact_point in contact.contact_points
            ]
            for contact in contacts
        ]

        for i_iteration in range(self.iterations):
            for i_contact, contact in enumerate(contacts):
                for i_point, contact_point in enumerate(contact.contact_points):
                    self._solve_contact_point(
                        contact,
                        contact_point,
                        inverse_effective_masses[i_contact][i_point],
                    )
