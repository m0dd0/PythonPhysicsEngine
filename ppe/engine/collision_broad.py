"""
Module containing abstract base classes for broad-phase collision detection strategies.

The broad-phase collision detection is the first step in the collision detection process.
It is responsible for finding all pairs of bodies that might be colliding with each other.
The found pairs are then passed to the narrow-phase collision detection for further processing.

This module contains the following classes:

- `AbstractBroadPhase`: An abstract base class for all broad-phase collision detection strategies.
- `BruteForceBroadPhase`: A dummy broad phase that will return all possible pairs of bodies as potential collision pairs.
- `AABBBroadPhase`: An efficient broad-phase using Axis-Aligned Bounding Boxes (AABB).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from ppe.engine.body import Body
from ppe.engine.common import Vec2
from ppe.engine.debug import DebugRecorder


class AbstractBroadPhase(ABC):
    """An abstract base class for all broad-phase collision detection strategies."""

    def __init__(self, debug_recorder: Optional[DebugRecorder] = None) -> None:
        """
        Initializes the broad-phase collision detection strategy.

        Args:
            debug_recorder: An optional debug drawer for visualizing the broad-phase.
        """
        self.debug_recorder = debug_recorder

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
        pass


class BruteForceBroadPhase(AbstractBroadPhase):
    """A simple O(n^2) broad-phase that checks every body against every other."""

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
            for body_b in bodies[i + 1 :]:
                # Static bodies do not need to be checked against each other
                if body_a.inverse_mass == 0 and body_b.inverse_mass == 0:
                    continue

                potential_pairs.append((body_a, body_b))
        return potential_pairs


class AABBBroadPhase(AbstractBroadPhase):
    """An efficient broad-phase using Axis-Aligned Bounding Boxes (AABB)."""

    def _aabbs_overlap(
        self, min_a: Vec2, max_a: Vec2, min_b: Vec2, max_b: Vec2
    ) -> bool:
        """
        Checks if two AABBs, defined by their min/max points, overlap.

        Args:
            min_a (Vec2): The minimum point of the first AABB.
            max_a (Vec2): The maximum point of the first AABB.
            min_b (Vec2): The minimum point of the second AABB.
            max_b (Vec2): The maximum point of the second AABB.

        Returns:
            bool: True if the two AABBs overlap, False otherwise.
        """
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
            bodies (List[Body]): A list of all Body objects in the simulation.

        Returns:
            List[Tuple[Body, Body]]: A list of tuples, where each tuple contains a pair of bodies
            that might be colliding.
        """
        # getting the AABBs of all bodies first prevents recalculating them multiple times
        # although we plan to use caching in the future, this is a good first step this is saver for now
        body_aabbs = [body.get_aabb() for body in bodies]

        # draw the AABBs for debugging purposes
        # if self.debug_recorder is not None:
        #     for body, (min_a, max_a) in zip(bodies, body_aabbs):
        #         self.debug_recorder.add_polygon(
        #             [min_a, Vec2(max_a.x, min_a.y), max_a, Vec2(min_a.x, max_a.y)],
        #             color=(0, 0, 255),
        #         )

        potential_pairs = []
        for i, (body_a, (min_a, max_a)) in enumerate(zip(bodies, body_aabbs)):
            for body_b, (min_b, max_b) in zip(bodies[i + 1 :], body_aabbs[i + 1 :]):
                if body_a.inverse_mass == 0 and body_b.inverse_mass == 0:
                    continue

                if self._aabbs_overlap(min_a, max_a, min_b, max_b):
                    potential_pairs.append((body_a, body_b))

                    # draw the overlapping AABBs for debugging purposes
                    if self.debug_recorder is not None:
                        self.debug_recorder.add_polygon(
                            [
                                min_a,
                                Vec2(max_a.x, min_a.y),
                                max_a,
                                Vec2(min_a.x, max_a.y),
                            ],
                            color=(255, 0, 0),
                        )
                        self.debug_recorder.add_polygon(
                            [
                                min_b,
                                Vec2(max_b.x, min_b.y),
                                max_b,
                                Vec2(min_b.x, max_b.y),
                            ],
                            color=(255, 0, 0),
                        )

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


class SpatialHashBroadPhase(AbstractBroadPhase):
    """A broad-phase using spatial hashing for efficient collision detection."""

    def __init__(self, debug_recorder: Optional[DebugRecorder] = None) -> None:
        super().__init__(debug_recorder)
        raise NotImplementedError("SpatialHashBroadPhase is not yet implemented.")

    def find_potential_pairs(self, bodies: List[Body]) -> List[Tuple[Body, Body]]:
        raise NotImplementedError("SpatialHashBroadPhase is not yet implemented.")
