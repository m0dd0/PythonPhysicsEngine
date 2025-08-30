from abc import ABC, abstractmethod
from typing import List

from ppe.engine.common import Body


class AbstractIntegrator(ABC):
    """An abstract base class for all motion integration strategies."""

    @abstractmethod
    def integrate_velocities(self, bodies: List[Body], dt: float) -> None:
        """
        Updates body velocities based on accumulated forces.

        Args:
            bodies: The list of all bodies in the simulation.
            dt: The time step for the frame.
        """
        raise NotImplementedError

    @abstractmethod
    def integrate_positions(self, bodies: List[Body], dt: float) -> None:
        """
        Updates body positions based on their current velocities.

        Args:
            bodies: The list of all bodies in the simulation.
            dt: The time step for the frame.
        """
        raise NotImplementedError


class NoOpIntegrator(AbstractIntegrator):
    """An integrator that performs no action, for debugging or simple kinematics."""

    def integrate_velocities(self, bodies: List[Body], dt: float) -> None:
        """Does nothing."""
        pass

    def integrate_positions(self, bodies: List[Body], dt: float) -> None:
        """Does nothing."""
        pass


class SemiImplicitEulerIntegrator(AbstractIntegrator):
    """A simple and stable integrator using the Semi-Implicit Euler method."""

    def __init__(self) -> None:
        """Initializes the Semi-Implicit Euler integrator."""
        pass

    def integrate_velocities(self, bodies: List[Body], dt: float) -> None:
        """Updates body velocities based on accumulated forces."""
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue

            # Update linear velocity
            linear_acceleration = body.force_accumulator * body.inverse_mass
            body.velocity += linear_acceleration * dt

            # Update angular velocity
            angular_acceleration = body.torque_accumulator * body.inverse_inertia
            body.angular_velocity += angular_acceleration * dt

    def integrate_positions(self, bodies: List[Body], dt: float) -> None:
        """Updates body positions based on their current velocities."""
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue

            # Update linear position
            body.position += body.velocity * dt

            # Update angular position (angle)
            body.angle += body.angular_velocity * dt


class PositionVerletIntegrator(AbstractIntegrator):
    """
    Updates motion using the Position Verlet integration method.
    This integrator is highly stable and designed to be paired with a
    position-based solver.
    This integrator requires that the solver only updates position and
    not velocity.
    """

    def __init__(self) -> None:
        """Initializes the Position Verlet integrator."""
        pass

    def integrate_velocities(self, bodies: List[Body], dt: float) -> None:
        """
        Performs the first step of Verlet integration, predicting a new
        provisional position for each body.
        """
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue

            # Store current position to become the previous position next frame
            current_position = body.position
            current_angle = body.angle

            # --- Update Linear Position ---
            # displacement = current_pos - previous_pos
            displacement = body.position - body.previous_position
            # new_pos = current_pos + displacement + acceleration * dt * dt
            acceleration = body.force_accumulator * body.inverse_mass
            body.position += displacement + acceleration * dt * dt

            # --- Update Angular Position ---
            angular_displacement = body.angle - body.previous_angle
            angular_acceleration = body.torque_accumulator * body.inverse_inertia
            body.angle += angular_displacement + (angular_acceleration * (dt * dt))

            # Update previous state for the next frame
            body.previous_position = current_position
            body.previous_angle = current_angle

    def integrate_positions(self, bodies: List[Body], dt: float) -> None:
        """
        Performs the second step of Verlet integration, deriving the final
        velocity from the change in position.
        This should be called *after* the position-based solver has run.
        """
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue

            # The solver may have corrected body.position. We use this
            # final position to derive the velocity for the frame.
            body.velocity = (body.position - body.previous_position) / dt
            body.angular_velocity = (body.angle - body.previous_angle) / dt
