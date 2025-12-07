"""Module defining joint classes for constraints between bodies in the physics engine."""

from abc import ABC

from ppe.engine.body import Body
from ppe.engine.common import Vec2


class Joint(ABC):
    """Base class for joints."""

    pass


class DistanceJoint(Joint):
    """A constraint that keeps two points on two bodies at a fixed distance."""

    def __init__(
        self,
        body_a: Body,
        body_b: Body,
        anchor_a: Vec2,
        anchor_b: Vec2,
        distance: float,
    ):
        """
        Initializes a new DistanceJoint instance.

        Args:
            body_a (Body): The first body.
            body_b (Body): The second body.
            anchor_a (Vec2): The anchor point on the first body.
            anchor_b (Vec2): The anchor point on the second body.
            distance (float): The desired distance between the anchor points.
        """
        self.body_a = body_a
        self.body_b = body_b
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        self.distance = distance


# TODO more joints
