# this can not be together in a file with the CollisionDetector class because of circular imports

import dataclasses

from ppe.vector import Vector
from ppe.bodies import Body


@dataclasses.dataclass
class Collision:
    bodyA: Body
    bodyB: Body
    normal: Vector  # normal points outwards from obj1 and is normalized
    depth: float
    penetrating_point: Vector
    # the penetrating point is the point of the object which is deepest inside the other object whose normal was used as the collision normal
