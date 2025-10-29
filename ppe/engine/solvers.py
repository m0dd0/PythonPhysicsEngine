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
    Resolves constraints by applying impulses iteratively.
    (This is the standard solver for most physics engines).
    """

    COMPATIBLE_INTEGRATORS = [SemiImplicitEulerIntegrator]

    def __init__(
        self, iterations: int = 30, debug_drawer: Optional[AbstractDebugDrawer] = None
    ):
        """
        Initializes the solver with the given number of iterations and an optional debug drawer.

        Args:
            iterations (int, optional): The number of iterations to perform when solving the constraints.
                Defaults to 30.
            debug_drawer (Optional[AbstractDebugDrawer]): An optional debug drawer for visualizing the simulation.
        """
        super().__init__(debug_drawer)
        self.iterations = iterations

    def _apply_impulse(self, body: Body, impulse: Vec2, contact_vector: Vec2):
        """Applies both linear and angular impulse to a body."""
        body.velocity += impulse * body.inverse_mass
        body.angular_velocity += contact_vector.cross(impulse) * body.inverse_inertia

    def _solve_contact(self, contact: Contact, dt: float):
        """Calculates and applies the impulse for a single contact manifold.
        
        Args:
            contact (Contact): The contact manifold to solve.
            dt (float): The time step for the solver.
        """
        body_ref = contact.reference_body  # reference body
        body_inc = contact.incident_body  # incident body
        normal = contact.normal

        # Process each contact point in the manifold
        for contact_point in contact.contact_points:
            r_a = contact_point - body_ref.position
            r_b = contact_point - body_inc.position

            # 1. Calculate the point velocity at the contact point. this is the bodies
            # velocity and angular velocity at the contact point.
            v_a = body_ref.velocity + Vec2(
                -body_ref.angular_velocity * r_a.y, body_ref.angular_velocity * r_a.x
            )
            v_b = body_inc.velocity + Vec2(
                -body_inc.angular_velocity * r_b.y, body_inc.angular_velocity * r_b.x
            )
            # relative velocity of both bodies at the contact point
            relative_velocity = v_b - v_a

            # component of relative velocity in the direction of the contact normal
            relative_normal_velocity = relative_velocity.dot(normal)
            print(f"relative_normal_velocity: {relative_normal_velocity}")

            # Do nothing if objects are already moving apart
            if relative_normal_velocity > 0:
                continue

            # 2. Calculate the effective mass
            # This represents how resistant the two bodies are to being pushed apart.
            r_a_perp_n = r_a.dot(normal)
            r_b_perp_n = r_b.dot(normal)

            effective_mass = (
                body_ref.inverse_mass
                + body_inc.inverse_mass
                + (r_a.cross(normal)) ** 2 * body_ref.inverse_inertia
                + (r_b.cross(normal)) ** 2 * body_inc.inverse_inertia
                + (r_a_perp_n * r_a_perp_n * body_ref.inverse_inertia)
                + (r_b_perp_n * r_b_perp_n * body_inc.inverse_inertia)
            )

            if effective_mass == 0.0:
                continue

            # 3. Calculate the impulse magnitude (j)
            e = min(body_ref.restitution, body_inc.restitution)
            j = -(1.0 + e) * relative_normal_velocity
            j /= effective_mass
            j /= len(
                contact.contact_points
            )  # Distribute impulse over all contact points

            # 4. Apply the impulse
            impulse = normal * j
            self._apply_impulse(body_ref, impulse * -1.0, r_a)
            self._apply_impulse(body_inc, impulse, r_b)

            # --- Positional Correction (Baumgarte Stabilization) ---
            # This applies a small extra impulse to push sinking objects apart.
            beta = 0.8  # Baumgarte stabilization factor
            positional_error = contact.penetration_depth
            bias_impulse_magnitude = (
                (beta / dt) * max(0.0, positional_error - 0.01) / effective_mass
            )
            bias_impulse_magnitude /= len(contact.contact_points)  # Distribute impulse

            bias_impulse = normal * bias_impulse_magnitude
            self._apply_impulse(body_ref, bias_impulse * -1.0, r_a)
            self._apply_impulse(body_ref, bias_impulse, r_b)

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        """
        Solves the given list of contacts and joints by updating the bodies' position and velocity.

        Notes:
            Joint solving is not implemented yet.

        Args:
            contacts (List[Contact]): A list of contacts to solve.
            joints (List[Joint]): A list of joints to solve.
            dt (float): The time step for the solver.
        """
        if len(joints) > 0:
            raise NotImplementedError("Joint solving is not implemented yet.")

        # The main loop that iterates multiple times to allow impulses to propagate
        for i in range(self.iterations):
            for contact in contacts:
                self._solve_contact(contact, dt)

        # Joint solving would go here in a similar loop
        # for joint in joints:
        #     self._solve_joint(joint, dt)


class PositionBasedSolver(AbstractSolver):
    COMPATIBLE_INTEGRATORS = [PositionVerletIntegrator]

    def __init__(
        self, iterations: int = 10, debug_drawer: Optional[AbstractDebugDrawer] = None
    ):
        super().__init__(debug_drawer)
        self.iterations = iterations

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        # TODO implement
        raise NotImplementedError("PositionBasedSolver is not implemented yet.")

# class LegacySolver(AbstractSolver):
#     COMPATIBLE_INTEGRATORS = [SemiImplicitEulerIntegrator]

#     def _solve_contact(self, contact: Contact, dt: float) -> None:
#         if (
#             contact.reference_body.inverse_mass == 0
#             and contact.incident_body.inverse_mass == 0
#         ):
#             return

#         # move objects so that they don't overlap anymore
#         if (
#             contact.reference_body.inverse_mass != 0
#             and contact.incident_body.inverse_mass != 0
#         ):
#             contact.reference_body.position -= contact.normal * (
#                 contact.penetration_depth / 2
#             )
#             contact.incident_body.position += contact.normal * (
#                 contact.penetration_depth / 2
#             )
#         elif contact.reference_body.inverse_mass == 0:
#             contact.incident_body.position += contact.normal * contact.penetration_depth
#         else:
#             contact.reference_body.position -= (
#                 contact.normal * contact.penetration_depth
#             )

#         # change velocities
#         # https://en.wikipedia.org/wiki/Collision_response
#         # https://www.chrishecker.com/images/e/e7/Gdmphys3.pdf
#         # not sure if min or average of bouncieness models reality better
#         e = (contact.reference_body.restitution + contact.incident_body.restitution) / 2
#         impulse = (
#             -(1 + e)
#             * (contact.reference_body.velocity - contact.incident_body.velocity).dot(
#                 contact.normal
#             )
#             / (contact.reference_body.inverse_mass + contact.incident_body.inverse_mass)
#         )

#         # avoid that fixed objects get a velocity value after a collision
#         if contact.reference_body.inverse_mass != 0:
#             contact.reference_body.velocity += (
#                 impulse / contact.reference_body.mass * contact.normal * dt
#             )
#         if contact.incident_body.inverse_mass != 0:
#             contact.incident_body.velocity -= (
#                 impulse / contact.incident_body.mass * contact.normal * dt
#             )

#     def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
#         for contact in contacts:
#             self._solve_contact(contact, dt)