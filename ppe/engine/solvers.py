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
    """An abstract base class for all constraint solver strategies."""

    COMPATIBLE_INTEGRATORS = []

    def __init__(self, debug_drawer: Optional[AbstractDebugDrawer] = None) -> None:
        self.debug_drawer = debug_drawer

    @abstractmethod
    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
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
        """Initializes the iterative solver."""
        super().__init__(debug_drawer)
        self.iterations = iterations

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        """Resolves collision contacts by applying impulses iteratively."""
        if len(joints) > 0:
            raise NotImplementedError("Joint solving is not implemented yet.")

        # The main loop that iterates multiple times to allow impulses to propagate
        for i in range(self.iterations):
            for contact in contacts:
                self._solve_contact(contact, dt)

        # Joint solving would go here in a similar loop
        # for joint in joints:
        #     self._solve_joint(joint, dt)

    def _apply_impulse(self, body: Body, impulse: Vec2, contact_vector: Vec2):
        """Applies both linear and angular impulse to a body."""
        body.velocity += impulse * body.inverse_mass
        body.angular_velocity += contact_vector.cross(impulse) * body.inverse_inertia

    def _solve_contact(self, contact: Contact, dt: float):
        """Calculates and applies the impulse for a single contact manifold."""
        body_a = contact.body_a
        body_b = contact.body_b
        normal = contact.normal

        # Process each contact point in the manifold
        for contact_point in contact.contact_points:
            r_a = contact_point - body_a.position
            r_b = contact_point - body_b.position

            # 1. Calculate the point velocity at the contact point. this is the bodies 
            # velocity and angular velocity at the contact point.
            v_a = body_a.velocity + Vec2(
                -body_a.angular_velocity * r_a.y, body_a.angular_velocity * r_a.x
            )
            v_b = body_b.velocity + Vec2(
                -body_b.angular_velocity * r_b.y, body_b.angular_velocity * r_b.x
            )
            # relative velocity of both bodies at the contact point
            relative_velocity = v_b - v_a

            # component of relative velocity in the direction of the contact normal
            relative_normal_velocity = relative_velocity.dot(normal)

            # Do nothing if objects are already moving apart
            if relative_normal_velocity > 0:
                continue

            # 2. Calculate the effective mass
            # This represents how resistant the two bodies are to being pushed apart.
            r_a_perp_n = r_a.dot(normal)
            r_b_perp_n = r_b.dot(normal)

            effective_mass = (
                body_a.inverse_mass
                + body_b.inverse_mass
                + (r_a.cross(normal))**2 * body_a.inverse_inertia
                + (r_b.cross(normal))**2 * body_b.inverse_inertia
                # + (r_a_perp_n * r_a_perp_n * body_a.inverse_inertia)
                # + (r_b_perp_n * r_b_perp_n * body_b.inverse_inertia)
            )

            if effective_mass == 0.0:
                continue

            # 3. Calculate the impulse magnitude (j)
            e = min(body_a.restitution, body_b.restitution)
            j = -(1.0 + e) * relative_normal_velocity
            j /= effective_mass
            j /= len(
                contact.contact_points
            )  # Distribute impulse over all contact points

            # 4. Apply the impulse
            impulse = normal * j
            self._apply_impulse(body_a, impulse * -1.0, r_a)
            self._apply_impulse(body_b, impulse, r_b)

            # --- Positional Correction (Baumgarte Stabilization) ---
            # This applies a small extra impulse to push sinking objects apart.
            # beta = 0.2  # Baumgarte stabilization factor
            # positional_error = contact.penetration_depth
            # bias_impulse_magnitude = (
            #     (beta / dt) * max(0.0, positional_error - 0.01) / effective_mass
            # )
            # bias_impulse_magnitude /= len(contact.contact_points)  # Distribute impulse

            # bias_impulse = normal * bias_impulse_magnitude
            # self._apply_impulse(body_a, bias_impulse * -1.0, r_a)
            # self._apply_impulse(body_b, bias_impulse, r_b)


class LegacySolver(AbstractSolver):
    COMPATIBLE_INTEGRATORS = [SemiImplicitEulerIntegrator]

    def _solve_contact(self, contact: Contact, dt: float) -> None:
        if contact.body_a.inverse_mass == 0 and contact.body_b.inverse_mass == 0:
            return

        # move objects so that they don't overlap anymore
        if contact.body_a.inverse_mass != 0 and contact.body_b.inverse_mass != 0:
            contact.body_a.position -= contact.normal * (contact.penetration_depth / 2)
            contact.body_b.position += contact.normal * (contact.penetration_depth / 2)
        elif contact.body_a.inverse_mass == 0:
            contact.body_b.position += contact.normal * contact.penetration_depth
        else:
            contact.body_a.position -= contact.normal * contact.penetration_depth

        # change velocities
        # https://en.wikipedia.org/wiki/Collision_response
        # https://www.chrishecker.com/images/e/e7/Gdmphys3.pdf
        # not sure if min or average of bouncieness models reality better
        e = (contact.body_a.restitution + contact.body_b.restitution) / 2
        impulse = (
            -(1 + e)
            * (contact.body_a.velocity - contact.body_b.velocity).dot(contact.normal)
            / (contact.body_a.inverse_mass + contact.body_b.inverse_mass)
        )

        # avoid that fixed objects get a velocity value after a collision
        if contact.body_a.inverse_mass != 0:
            contact.body_a.velocity += (
                impulse / contact.body_a.mass * contact.normal * dt
            )
        if contact.body_b.inverse_mass != 0:
            contact.body_b.velocity -= (
                impulse / contact.body_b.mass * contact.normal * dt
            )

    def solve(self, contacts: List[Contact], joints: List[Joint], dt: float) -> None:
        for contact in contacts:
            self._solve_contact(contact, dt)


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
