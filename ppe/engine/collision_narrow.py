from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict

from ppe.engine.common import Body, Contact
from ppe.engine.collision_handlers import (
    AbstractCollisionHandler,
    CircleVsCircleHandler,
    SatPolygonHandler,
    CircleVsPolygonHandler,
)
from ppe.engine.debug import AbstractDebugDrawer

SHAPE_TYPE_TO_ID = {
    "circle": 0,
    "polygon": 1,
    # "compound": 2,
}


class AbstractNarrowPhase(ABC):
    """An abstract base class for narrow-phase collision detection strategies."""

    def __init__(self, debug_drawer: Optional[AbstractDebugDrawer] = None):
        """
        Initializes the narrow-phase with an optional debug drawer.

        Args:
            debug_drawer: An optional debug drawer for visualizing collisions.
        """
        self.debug_drawer = debug_drawer

    @abstractmethod
    def generate_contacts(
        self, potential_pairs: List[Tuple[Body, Body]]
    ) -> List[Contact]:
        """
        Takes potential pairs from the broad phase and returns a list of
        confirmed contacts with their collision data.
        """
        raise NotImplementedError


class DispatchNarrowPhase(AbstractNarrowPhase):
    """A narrow-phase strategy that dispatches to specific handler objects."""

    def __init__(
        self,
        handlers: Dict[Tuple[str, str], AbstractCollisionHandler] = None,
        debug_drawer: Optional[AbstractDebugDrawer] = None,
    ):
        """
        Initializes the dispatcher with a map of shape-type pair keys to
        concrete handler objects.

        Args:
            handlers: A dictionary mapping an integer key to a handler object.
        """
        super().__init__(debug_drawer)

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
        self._collision_handlers = {
            (
                min(SHAPE_TYPE_TO_ID[key[0]], SHAPE_TYPE_TO_ID[key[1]]),
                max(SHAPE_TYPE_TO_ID[key[0]], SHAPE_TYPE_TO_ID[key[1]]),
            ): handler
            for key, handler in handlers.items()
        }

    @property
    def debug_drawer(self) -> Optional[AbstractDebugDrawer]:
        """Returns the debug drawer for visualizing collisions."""
        return self._debug_drawer
    
    @debug_drawer.setter
    def debug_drawer(self, drawer: Optional[AbstractDebugDrawer]):
        """Sets the debug drawer for visualizing collisions."""
        self._debug_drawer = drawer

        for handler in self._collision_handlers.values():
            handler.debug_drawer = drawer

    def _dispatch_collision(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """Finds and calls the correct handler for a pair of bodies."""
        id_a = SHAPE_TYPE_TO_ID[body_a.shape.get_type()]
        id_b = SHAPE_TYPE_TO_ID[body_b.shape.get_type()]

        handler = self._collision_handlers.get((min(id_a, id_b), max(id_a, id_b)))

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
        Takes potential collision pairs and returns a list of confirmed contacts.
        """
        contacts = []
        for body_a, body_b in potential_pairs:
            contact_info = self._dispatch_collision(body_a, body_b)
            if contact_info:
                contacts.append(contact_info)

                if self.debug_drawer:
                    # Draw the contact normal going out from body_a
                    self.debug_drawer.draw_line(
                        body_a.position,
                        body_a.position + contact_info.normal * contact_info.penetration_depth,
                        color=(255, 0, 0),  # Red for contact normal
                        arrow=True,
                    )
                    # visualize the penetration depth with the circle radius
                    self.debug_drawer.draw_circle(
                        body_a.position,
                        contact_info.penetration_depth * 10, # scale for visibility
                        color=(0, 255, 0),
                    )

        return contacts
