# this can not be together in a file with the CollisionDetector class because of circular imports

import dataclasses

from ppe.vector import Vector
from ppe.bodies import Body


@dataclasses.dataclass
class Collision:
    """The Collision class is a data class that holds information about a collision between two bodies.
    It is used in the narrow phase collision detection to store information about the collision which can be used to resolve the collision.
    By defintion bodyA gets penetrated by bodyB.
    The normal points outwards from bodyA and is normalized.
    The penetrating point is the point of bodyB which is inside bodyA.
    If a collision occurs where 2 points are penetrating at the same depth, two collisions are created.
    """

    bodyA: Body  # gets penetrated
    bodyB: Body  # penetrates bodyA
    normal: Vector  # normal points outwards from objA and is normalized
    depth: float
    penetrating_point: Vector  # penetrating point of objB in objA
