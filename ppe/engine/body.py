from typing import Tuple, Union

from ppe.engine.common import Vec2
from ppe.engine.shapes import Shape


class Body:
    """Represents a single physical object in the world."""

    def __init__(
        self,
        shape: Shape,
        position: Vec2,
        mass: Union[float, None],
        angle: float = 0.0,
        restitution: float = 0.2,
        friction_coefficient: float = 0.5,
        initial_velocity: Vec2 = Vec2(0, 0),
        initial_angular_velocity: float = 0.0,
        user_data: dict = None,
    ):
        """
        Initializes a new Body instance.

        Args:
            shape (Shape): The shape of the body.
            position (Vec2): The initial position of the body.
            mass (Union[float, None]): The mass of the body. If None, the body is
                considered static.
            angle (float, optional): The initial rotation angle of the body in radians.
                Defaults to 0.0.
            restitution (float, optional): The restitution (bounciness) of the body.
                Defaults to 0.2.
            friction_coefficient (float, optional): The friction coefficient of the body.
                Defaults to 0.5.
            initial_velocity (Vec2, optional): The initial linear velocity of the body.
                Defaults to (0, 0).
            initial_angular_velocity (float, optional): The initial angular velocity of the body.
                Defaults to 0.0.
            user_data (dict, optional): Custom user data associated with the body.
                This data is irrelevant for the physics simulation but might be for
                other purposes like rendering. Defaults to None.

        Raises:
            ValueError: If the mass is not positive or None.
        """
        if mass is not None and mass <= 0:
            raise ValueError("Mass must be positive or None.")

        self.shape = shape
        self.position = position
        self.angle = angle

        self.previous_position: Vec2 = (
            self.position
        )  # used by some integrators like Verlet
        self.previous_angle: float = self.angle  # used by some integrators like Verlet

        self.velocity: Vec2 = initial_velocity
        self.angular_velocity: float = initial_angular_velocity

        self.force_accumulator: Vec2 = Vec2(0, 0)
        self.torque_accumulator: float = 0.0

        self.mass = mass
        self.restitution = restitution
        self.friction_coefficient = friction_coefficient

        if self.mass is None:
            self.inverse_mass: float = 0.0
            self.inverse_inertia: float = 0.0
        else:
            self.inverse_mass: float = 1.0 / mass
            self.inverse_inertia: float = 1.0 / self.shape.calculate_inertia(mass)

        self.user_data = user_data if user_data is not None else dict()

    @classmethod
    def create_with_density(
        cls, shape: "Shape", density: float, *args, **kwargs
    ) -> "Body":
        """Alternative initializer to create a new Body instance with a specific density.

        Args:
            shape (Shape): The shape of the body.
            density (float): The density of the body.
            *args: Additional positional arguments to pass to the Body constructor.
            **kwargs: Additional keyword arguments to pass to the Body constructor.

        Returns:
            Body: The newly created body instance.
        """
        mass = shape.get_area() * density
        return cls(shape=shape, mass=mass, *args, **kwargs)

    def clear_forces(self) -> None:
        self.force_accumulator = Vec2(0, 0)
        self.torque_accumulator = 0.0

    def get_aabb(self) -> Tuple[Vec2, Vec2]:
        """
        Calculates the Axis-Aligned Bounding Box (AABB) of the body in world space.

        Returns:
            A tuple containing the min and max points of the AABB.
        """
        return self.shape.get_aabb(self.position, self.angle)

    def is_point_inside(self, point: Vec2) -> bool:
        """
        Checks if a point is inside the body in world space.

        Args:
            point: The point to check.

        Returns:
            True if the point is inside the body, False otherwise.
        """
        return self.shape.is_point_inside(point, self.position, self.angle)
