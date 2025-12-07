"""
Module containing the narrow-phase collision detection strategy.

The narrow-phase collision detection is the second step in the collision detection process.
It is responsible for finding the contacts between two bodies that are determined to be colliding by the broad-phase collision detection.
Currently, we use a dispatcher that dispatches to specific handler objects for each combination of shape types.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from ppe.engine.collision_handlers import (
    AbstractCollisionHandler,
    CircleVsCircleHandler,
    CircleVsPolygonHandler,
    SatPolygonHandler,
)
from ppe.engine.common import Body, Contact
from ppe.engine.debug import DebugRecorder

# we associate shape types with integer IDs so we can define an order of the types
# this is important so that the argument order of the collision handlers are consistent
SHAPE_TYPE_TO_ID = {
    "circle": 0,
    "polygon": 1,
    # "compound": 2,
}


class AbstractNarrowPhase(ABC):
    """An abstract base class for narrow-phase collision detection strategies."""

    def __init__(self, debug_recorder: Optional[DebugRecorder] = None):
        """
        Initializes the narrow-phase with an optional debug drawer.

        Args:
            debug_recorder (DebugRecorder, optional): An optional debug drawer for visualizing collisions.
        """
        self.debug_recorder = debug_recorder

    @abstractmethod
    def generate_contacts(
        self, potential_pairs: List[Tuple[Body, Body]]
    ) -> List[Contact]:
        """
        Takes potential pairs from the broad phase and returns a list of
        confirmed contacts with their collision data.

        Args:
            potential_pairs (List[Tuple[Body, Body]]): A list of tuples, where each tuple contains a pair of bodies
            that might be colliding.

        Returns:
            List[Contact]: A list of Contact objects.
        """
        raise NotImplementedError


class DispatchNarrowPhase(AbstractNarrowPhase):
    """A narrow-phase strategy that dispatches to specific handler objects."""

    def __init__(
        self,
        handlers: Dict[Tuple[str, str], AbstractCollisionHandler] = None,
        debug_recorder: Optional[DebugRecorder] = None,
    ):
        """
        Initializes the dispatcher with a map of shape-type pair keys to
        concrete handler objects.

        Args:
            handlers (Dict[Tuple[str, str], AbstractCollisionHandler], optional): A dictionary mapping an integer key to a handler object.
                Defaults to a default handler map.
            debug_recorder (DebugRecorder, optional): An optional debug drawer for visualizing collisions.
        """
        if handlers is None:
            handlers = {
                ("circle", "circle"): CircleVsCircleHandler(),
                ("circle", "polygon"): CircleVsPolygonHandler(),
                ("polygon", "polygon"): SatPolygonHandler(),
            }
        # check that no combinations appear twice
        for key, handler in handlers.items():
            if not isinstance(handler, AbstractCollisionHandler):
                raise TypeError(
                    f"Handler for {key} must be an AbstractCollisionHandler instance."
                )

        if not len(set([frozenset(key) for key in handlers.keys()])) == len(handlers):
            raise ValueError(
                "Collision handlers must be unique for each shape type pair."
            )

        # convert the keys to ordered pairs of shape type IDs
        self.collision_handlers = {
            (
                min(SHAPE_TYPE_TO_ID[key[0]], SHAPE_TYPE_TO_ID[key[1]]),
                max(SHAPE_TYPE_TO_ID[key[0]], SHAPE_TYPE_TO_ID[key[1]]),
            ): handler
            for key, handler in handlers.items()
        }

        # must be set after the _collision_handlers attribute is initialized
        super().__init__(debug_recorder)

    def _dispatch_collision(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """
        Finds and calls the correct handler for a pair of bodies based on the shape type of each body.

        Args:
            body_a (Body): The first body.
            body_b (Body): The second body.

        Returns:
            Optional[Contact]: The contact information if a collision is detected, otherwise None.
        """
        id_a = SHAPE_TYPE_TO_ID[body_a.shape.get_type()]
        id_b = SHAPE_TYPE_TO_ID[body_b.shape.get_type()]

        handler = self.collision_handlers.get((min(id_a, id_b), max(id_a, id_b)))

        if handler is None:
            # Fail loudly if no handler is registered for this pair.
            raise NotImplementedError(
                f"No collision handler for type pair ({body_a.shape.get_type()}, {body_b.shape.get_type()})"
            )

        # For non-symmetric handlers, ensure the argument order is correct.
        if id_a > id_b:
            return handler.generate_contact(body_b, body_a)
        else:
            return handler.generate_contact(body_a, body_b)

    def generate_contacts(
        self, potential_pairs: List[Tuple[Body, Body]]
    ) -> List[Contact]:
        """
        Takes a list of potential collision pairs and returns a list of confirmed contacts.

        Each contact represents a collision between two bodies and contains information about the collision,
        such as the reference body, the incident body, the collision normal, penetration depth, and contact points.

        Args:
            potential_pairs (List[Tuple[Body, Body]]): A list of tuples, where each tuple contains a pair of bodies
                that might be colliding.

        Returns:
            List[Contact]: A list of Contact objects, each representing a confirmed collision.
        """
        contacts = []
        for body_a, body_b in potential_pairs:
            contact_info = self._dispatch_collision(body_a, body_b)
            if contact_info:
                contacts.append(contact_info)

                # draw the contact points
                if self.debug_recorder is not None:
                    for point in contact_info.contact_points:
                        self.debug_recorder.add_marker(point, color=(255, 0, 0))
                        self.debug_recorder.add_marker_line(
                            point,
                            contact_info.normal,
                            color=(255, 0, 0),
                            arrow=True,
                        )

        return contacts
