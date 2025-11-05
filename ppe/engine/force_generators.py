
"""
This module contains classes for generating forces in a physics simulation.

A force generator is responsible for calculating and applying forces to physics bodies.
This module defines the abstract base class, `AbstractForceGenerator`, which all force generators must implement.
The available force generators are:

- `GlobalForceField`: Applies a constant force to all bodies in the simulation.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ppe.engine.common import Body, Vec2, Shape

class AbstractForceGenerator(ABC):
    """Abstract base class for force generators."""
    @abstractmethod
    def apply(self, bodies: Optional[List[Body]]) -> None:
        """
        Applies a force. Implementations update the passed bodies force accumulators in place.

        Args:
            bodies (List[Body]): The list of all bodies in the world. This is primarily
                    for global forces like gravity. Targeted forces might ignore this.
        """
        raise NotImplementedError
    
class GlobalForceField(AbstractForceGenerator):
    """Applies a constant force to all bodies in the simulation."""
    def __init__(self, strength: Vec2):
        """
        Initializes a global force field.

        Args:
            strength (Vec2): The force vector to apply to all bodies.
        """
        self.strength = strength

    def apply(self, bodies: Optional[List[Body]]) -> None:
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue
            body.force_accumulator += self.strength * body.mass

class LocalForceField(AbstractForceGenerator):
    def __init__(self, shape: Shape, strength: Vec2, shape_position: Vec2 = None, shape_angle: float = None):
        """
        Initializes a local force field that applies a force to all bodies inside a vritual shape.

        Args:
            shape: The shape to which this force applies.
            shape_position: The position of the shape in world coordinates.
            shape_angle: The angle of the shape in radians.
            strength: The force vector to apply at the shape's position.
        """
        self.shape = shape
        self.shape_position = shape_position
        self.shape_angle = shape_angle
        self.strength = strength

    def apply(self, bodies: Optional[List[Body]]) -> None:
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue
            
            # The logic is now a simple, generic call
            if self.shape.is_point_inside(
                point=body.position,
                position=self.shape_position,
                angle=self.shape_angle
            ):
                body.force_accumulator += self.strength

# TODO add sprong force etc