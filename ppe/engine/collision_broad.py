
from abc import ABC, abstractmethod
from typing import List, Tuple

from core import Body, Vec2

class AbstractBroadPhase(ABC):
    """An abstract base class for all broad-phase collision detection strategies."""

    @abstractmethod
    def find_potential_pairs(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        """
        Takes a list of all bodies and returns a list of potentially
        colliding pairs.

        Args:
            bodies: A list of all Body objects in the simulation.

        Returns:
            A list of tuples, where each tuple contains a pair of bodies
            that might be colliding.
        """
        raise NotImplementedError

class BruteForceBroadPhase(AbstractBroadPhase):
    """A simple O(n^2) broad-phase that checks every body against every other."""

    def __init__(self) -> None:
        """Initializes the BruteForceBroadPhase strategy."""
        pass

    def find_potential_pairs(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        """
        Takes a list of all bodies and returns a list of every possible
        colliding pair.

        Args:
            bodies: A list of all Body objects in the simulation.

        Returns:
            A list of tuples, where each tuple contains a pair of bodies
            that might be colliding.
        """
        potential_pairs = []
        for i, body_a in enumerate(bodies):
            for body_b in bodies[i + 1:]:
                # Static bodies do not need to be checked against each other
                if body_a.inverse_mass == 0 and body_b.inverse_mass == 0:
                    continue
                
                potential_pairs.append((body_a, body_b))
        return potential_pairs

class AABBBroadPhase(AbstractBroadPhase):
    """An efficient broad-phase using Axis-Aligned Bounding Boxes (AABB)."""

    def __init__(self) -> None:
        """Initializes the AABBBroadPhase strategy."""
        pass

    def _aabbs_overlap(self, min_a: Vec2, max_a: Vec2, min_b: Vec2, max_b: Vec2) -> bool:
        """Checks if two AABBs, defined by their min/max points, overlap."""
        if max_a.x < min_b.x or min_a.x > max_b.x:
            return False
        if max_a.y < min_b.y or min_a.y > max_b.y:
            return False
        return True

    def find_potential_pairs(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        """
        Takes a list of all bodies and returns a list of pairs whose
        bounding boxes overlap.

        Args:
            bodies: A list of all Body objects in the simulation.

        Returns:
            A list of tuples, where each tuple contains a pair of bodies
            that might be colliding.
        """
        # getting the AABBs of all bodies first prevents recalculating them multiple times
        # although we plan to use caching in the future, this is a good first step this is saver for now
        body_aabbs = [body.get_aabb() for body in bodies]

        potential_pairs = []
        for i, (body_a, (min_a, max_a)) in enumerate(zip(bodies, body_aabbs)):
            for body_b, (min_b, max_b) in zip(bodies[i + 1:], body_aabbs[i + 1:]):

                if body_a.inverse_mass == 0 and body_b.inverse_mass == 0:
                    continue

                if self._aabbs_overlap(min_a, max_a, min_b, max_b):
                    potential_pairs.append((body_a, body_b))

        # version without slicing might be a tiny bit faster:
        # for i in range(len(bodies)):
        #     body_a, (min_a, max_a) = bodies[i], body_aabbs[i]
        #     for j in range(i + 1, len(bodies)):
        #         body_b, (min_b, max_b) = bodies[j], body_aabbs[j]

        #         if body_a.inverse_mass == 0 and body_b.inverse_mass == 0:
        #             continue

        #         if self._aabbs_overlap(min_a, max_a, min_b, max_b):
        #             potential_pairs.append((body_a, body_b))

        return potential_pairs