from typing import List, Tuple
import abc

from _ppe.bodies import Body


class BroadPhaseBase(abc.ABC):
    """The BroadPhaseBase class is an abstract class for broad phase collision detection.
    It is used to reduce the number of pairs of bodies that are checked for collision in the narrow phase.
    The interface is a single method __call__ which takes a list of bodies and returns a list of pairs of bodies that are collision candidates.
    Optionally, you can add configuration options to the constructor of the class.
    """

    @abc.abstractmethod
    def __call__(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        """Checks for collision candidates in the given list of bodies.

        Args:
            bodies (List[Body]): A list of bodies for which to check for collision candidates.

        Returns:
            List[Tuple[Body, Body]]: A list of pairs of bodies that are collision candidates.
        """
        raise NotImplementedError


class AABB(BroadPhaseBase):
    """The AABB class is a broad phase collision detection algorithm that uses axis-aligned bounding boxes (AABB).
    It is a simple and fast algorithm that can be used as a first step to reduce the number of pairs of bodies that are checked for collision in the narrow phase.
    The algorithm works by checking if the AABBs of two bodies overlap.
    """

    def __call__(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        collision_candidates = []
        for i, body1 in enumerate(bodies):
            for body2 in bodies[i + 1 :]:
                if body1.kinematic and body2.kinematic:
                    continue
                if (
                    body1.shape.bbox[1].x < body2.shape.bbox[0].x
                    or body1.shape.bbox[0].x > body2.shape.bbox[1].x
                ):
                    continue
                if (
                    body1.shape.bbox[1].y < body2.shape.bbox[0].y
                    or body1.shape.bbox[0].y > body2.shape.bbox[1].y
                ):
                    continue
                collision_candidates.append((body1, body2))

        return collision_candidates
