"""
Module containing classes for motion integration strategies.

This module defines an abstract base class, `AbstractIntegrator`,
and several concrete implementations for different motion integration strategies.
The available integrators are:

- `SemiImplicitEulerIntegrator`: A semi-implicit Euler integrator.
- `PositionVerletIntegrator`: A position Verlet integrator.
- `NoOpIntegrator`: A dummy integrator that does not update the simulation state.

These integrators are designed to be modular and configurable, allowing for
easy customization of the motion integration strategy in different simulation
scenarios.
However, note that not all solvers can be used with all integrators and vice versa.
"""

from abc import ABC, abstractmethod
from typing import List

from ppe.engine.body import Body


class AbstractIntegrator(ABC):
    """An abstract base class for all motion integration strategies."""

    @abstractmethod
    def pre_solve_integration(self, bodies: List[Body], dt: float) -> None:
        """
        Updates body velocities based on accumulated forces.

        Args:
            bodies (List[Body]): The list of all bodies in the simulation.
            dt (float): The time step for the frame.
        """
        raise NotImplementedError

    @abstractmethod
    def post_solve_integration(self, bodies: List[Body], dt: float) -> None:
        """
        Updates body positions based on their current velocities.

        Args:
            bodies (List[Body]): The list of all bodies in the simulation.
            dt (float): The time step for the frame.
        """
        raise NotImplementedError


class NoOpIntegrator(AbstractIntegrator):
    """An integrator that performs no action, for debugging or simple kinematics."""

    def pre_solve_integration(self, bodies: List[Body], dt: float) -> None:
        """Does nothing.

        Args:
            bodies (List[Body]): The list of all bodies in the simulation.
            dt (float): The time step for the frame.
        """
        pass

    def post_solve_integration(self, bodies: List[Body], dt: float) -> None:
        """Does nothing.

        Args:
            bodies (List[Body]): The list of all bodies in the simulation.
            dt (float): The time step for the frame.
        """
        pass


class SemiImplicitEulerIntegrator(AbstractIntegrator):
    """A simple and stable integrator using the Semi-Implicit Euler method."""

    def __init__(self) -> None:
        """Initializes the Semi-Implicit Euler integrator."""
        pass

    def pre_solve_integration(self, bodies: List[Body], dt: float) -> None:
        """Updates body velocities based on accumulated forces.

        Args:
            bodies (List[Body]): The list of all bodies in the simulation.
            dt (float): The time step for the frame.
        """
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue

            # Update linear velocity
            linear_acceleration = body.force_accumulator * body.inverse_mass
            body.velocity += linear_acceleration * dt

            # Update angular velocity
            angular_acceleration = body.torque_accumulator * body.inverse_inertia
            body.angular_velocity += angular_acceleration * dt

    def post_solve_integration(self, bodies: List[Body], dt: float) -> None:
        """Updates body positions based on their current velocities.

        Args:
            bodies (List[Body]): The list of all bodies in the simulation.
            dt (float): The time step for the frame.
        """
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
    This integrator is designed to be paired with aposition-based solver.
    This integrator requires that the solver only updates position and
    not velocity.
    """

    def __init__(self) -> None:
        """Initializes the Position Verlet integrator."""
        pass

    def pre_solve_integration(self, bodies: List[Body], dt: float) -> None:
        """
        Performs the first step of Verlet integration, predicting a new
        provisional position for each body.

        Args:
            bodies (List[Body]): The list of all bodies in the simulation.
            dt (float): The time step for the frame.
        """
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue

            # Store current position to become the previous position next frame
            current_position = body.position
            current_angle = body.angle

            # --- Update Linear Position ---
            displacement = body.position - body.previous_position
            acceleration = body.force_accumulator * body.inverse_mass
            body.position += displacement + acceleration * dt * dt

            # --- Update Angular Position ---
            angular_displacement = body.angle - body.previous_angle
            angular_acceleration = body.torque_accumulator * body.inverse_inertia
            body.angle += angular_displacement + (angular_acceleration * (dt * dt))

            # Update previous state for the next frame
            body.previous_position = current_position
            body.previous_angle = current_angle

    def post_solve_integration(self, bodies: List[Body], dt: float) -> None:
        """
        Performs the second step of Verlet integration, deriving the final
        velocity from the change in position.
        This should be called *after* the position-based solver has run.

        Args:
            bodies (List[Body]): The list of all bodies in the simulation.
            dt (float): The time step for the frame.
        """
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue

            # The solver may have corrected body.position. We use this
            # final position to derive the velocity for the frame.
            body.velocity = (body.position - body.previous_position) / dt
            body.angular_velocity = (body.angle - body.previous_angle) / dt
