from abc import ABC, abstractmethod
from typing import List, Optional

from ppe.engine.common import Body, Vec2, Shape

class AbstractForceGenerator(ABC):
    @abstractmethod
    def apply(self, bodies: Optional[List[Body]]) -> None:
        """
        Applies a force.

        Args:
            bodies: The list of all bodies in the world. This is primarily
                    for global forces like gravity. Targeted forces will
                    ignore this and use their stored body references.
        """
        raise NotImplementedError
    
class GlobalForceField(AbstractForceGenerator):
    def __init__(self, strength: Vec2):
        self.strength = strength

    def apply(self, bodies: Optional[List[Body]]) -> None:
        for body in bodies:
            if body.inverse_mass == 0.0:
                continue
            body.force_accumulator += self.strength * body.mass

class LocalForceField(AbstractForceGenerator):
    def __init__(self, shape: Shape, strength: Vec2, shape_position: Vec2 = None, shape_angle: float = None):
        """
        Initializes a local force field.

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