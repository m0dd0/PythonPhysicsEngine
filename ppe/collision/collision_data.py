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
    contact_point_1: Vector
