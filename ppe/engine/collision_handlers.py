import math
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from ppe.engine.common import Body, CircleShape, PolygonShape, Contact, Vec2
from ppe.engine.debug import AbstractDebugDrawer


class AbstractCollisionHandler(ABC):
    """Defines the interface for a specific collision handler between two shapes."""

    def __init__(self, debug_drawer: Optional[AbstractDebugDrawer] = None):
        """
        Initializes the collision handler.

        Args:
            debug_drawer: An optional debug drawer for visualizing collisions.
        """
        self.debug_drawer = debug_drawer

    @abstractmethod
    def generate_contact(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """
        Takes two bodies and returns a Contact object if they collide,
        otherwise returns None.

        Args:
            body_a: The first body.
            body_b: The second body.

        Returns:
            A Contact object if a collision occurred, otherwise None.
        """
        pass


class CircleVsCircleHandler(AbstractCollisionHandler):
    """Generates contacts for two colliding circles."""

    def generate_contact(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """Checks for collision between two circles."""
        assert body_a.shape.get_type() == "circle"
        assert body_b.shape.get_type() == "circle"

        shape_a: CircleShape = body_a.shape
        shape_b: CircleShape = body_b.shape

        a_to_b = body_b.position - body_a.position
        sum_radii = shape_a.radius + shape_b.radius

        dist_sq = a_to_b.length_squared()

        if self.debug_drawer:
            # draw line from body_a to body_b in blue
            self.debug_drawer.draw_line(
                body_a.position, body_b.position, color=(0, 0, 255), arrow=True
            )

        if dist_sq >= sum_radii * sum_radii:
            return None

        if self.debug_drawer:
            # draw line from body_a to body_b in red
            self.debug_drawer.draw_line(
                body_a.position, body_b.position, color=(255, 0, 0), arrow=True
            )

        dist = math.sqrt(dist_sq)
        penetration = sum_radii - dist
        normal = a_to_b.normalize()

        return Contact(body_a, body_b, normal, penetration)


class SatPolygonHandler(AbstractCollisionHandler):
    """Generates contacts for two colliding convex polygons using SAT."""

    def _project(self, vertices: List[Vec2], axis: Vec2) -> Tuple[float, float]:
        """Projects a polygon's vertices onto an axis."""
        min_proj = float("inf")
        max_proj = float("-inf")
        for v in vertices:
            proj = v.dot(axis)
            min_proj = min(min_proj, proj)
            max_proj = max(max_proj, proj)
        return min_proj, max_proj

    def generate_contact(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """Checks for collision using the Separating Axis Theorem."""
        assert body_a.shape.get_type() == "polygon"
        assert body_b.shape.get_type() == "polygon"

        shape_a: PolygonShape = body_a.shape
        shape_b: PolygonShape = body_b.shape

        verts_a = shape_a.get_world_space_vertices(body_a.position, body_a.angle)
        verts_b = shape_b.get_world_space_vertices(body_b.position, body_b.angle)

        min_overlap = float("inf")
        collision_normal = None

        # Combine axes (prependicular to edges) from both polygons
        axes = []
        for verts in (verts_a, verts_b):
            for i, vert_i in enumerate(verts):
                edge = verts[(i + 1) % len(verts)] - vert_i
                axes.append(Vec2(-edge.y, edge.x).normalize())
                if self.debug_drawer:
                    self.debug_drawer.draw_line(
                        vert_i,
                        vert_i + Vec2(-edge.y, edge.x),
                        arrow=True,
                        color=(0, 0, 0),
                    )

        for axis in axes:
            # check if the projection of the two polygons on this axis overlaps
            min_a_proj, max_a_proj = self._project(verts_a, axis)
            min_b_proj, max_b_proj = self._project(verts_b, axis)

            overlap = min(max_a_proj, max_b_proj) - max(min_a_proj, min_b_proj)
            if overlap <= 0:
                return None  # Found a separating axis

            if overlap < min_overlap:
                min_overlap = overlap
                collision_normal = axis

        assert (
            collision_normal is not None
        ), "Collision normal should be set if we reach here."
        assert (
            0 < min_overlap < float("inf")
        ), "Overlap should be a positive finite value."

        # Ensure the normal points from body A to body B
        if (body_b.position - body_a.position).dot(collision_normal) < 0:
            collision_normal = collision_normal * -1.0

        return Contact(body_a, body_b, collision_normal, min_overlap)


class CircleVsPolygonHandler(AbstractCollisionHandler):
    """Generates contacts for a circle and a polygon."""

    def generate_contact(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """Checks for collision between a circle and a polygon."""
        # if isinstance(body_b.shape, CircleShape):
        #     body_a, body_b = body_b, body_a
        assert body_a.shape.get_type() == "circle"
        assert body_b.shape.get_type() == "polygon"

        circle_shape: CircleShape = body_a.shape
        poly_shape: PolygonShape = body_b.shape

        verts = poly_shape.get_world_space_vertices(body_b.position, body_b.angle)
        closest_point = None
        min_dist_sq = float("inf")

        for i, p1 in enumerate(verts):
            # compute wdge vector on the polygon and the vector from the circle center to the polygon vertices on the edge
            p2 = verts[(i + 1) % len(verts)]
            edge = p2 - p1  # from p1 to p2
            line_vec = body_a.position - p1  # from p1 to circle center

            # Project the circle center onto the edge to find the closest point
            t = line_vec.dot(edge) / edge.length_squared()
            t = max(
                0, min(1, t)
            )  # clamp t to [0, 1] (0 means closest point on the line is p1, 1 means p2)
            closest_on_edge = p1 + edge * t

            if self.debug_drawer:
                # draw line from circle center to closest point on edge in blue
                self.debug_drawer.draw_line(
                    body_a.position, closest_on_edge, color=(0, 0, 255)
                )

            dist_sq = (body_a.position - closest_on_edge).length_squared()
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_point = closest_on_edge

        assert (
            closest_point is not None
        ), "Closest point should be set if we reach here."

        if min_dist_sq >= circle_shape.radius * circle_shape.radius:
            return None

        dist = math.sqrt(min_dist_sq)
        normal = (body_a.position - closest_point).normalize()
        penetration = circle_shape.radius - dist

        return Contact(body_a, body_b, normal, penetration)
