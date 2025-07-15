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

        # if self.debug_drawer:
        #     # draw line from body_a to body_b in blue
        #     self.debug_drawer.draw_line(
        #         body_a.position, body_b.position, color=(0, 0, 255), arrow=True
        #     )

        if dist_sq >= sum_radii * sum_radii:
            return None

        dist = math.sqrt(dist_sq)
        penetration = sum_radii - dist
        normal = a_to_b.normalize()
        contact_point = body_a.position + normal * shape_a.radius

        return Contact(body_a, body_b, normal, penetration, [contact_point])


class SatPolygonHandler(AbstractCollisionHandler):
    """Generates contacts for two colliding convex polygons using SAT."""

    def _project_minmax(self, vertices: List[Vec2], axis: Vec2) -> Tuple[float, float]:
        """Projects a polygon's vertices onto an axis."""
        min_proj = float("inf")
        max_proj = float("-inf")
        for v in vertices:
            proj = v.dot(axis)
            min_proj = min(min_proj, proj)
            max_proj = max(max_proj, proj)
        return min_proj, max_proj

    def _clip_incident_edge(
        self,
        incident_edge: Tuple[Vec2, Vec2],
        clip_plane_normal: Vec2,
        clip_plane_offset: float,
    ) -> Tuple[Vec2, Vec2]:
        v1, v2 = incident_edge
        clipped_points = []

        # Calculate the signed distance from each vertex to the plane (>= 0 means inside the plane)
        d1 = v1.dot(clip_plane_normal) - clip_plane_offset
        d2 = v2.dot(clip_plane_normal) - clip_plane_offset

        # Keep points that are on the "inside" of the plane
        if d1 >= 0:
            clipped_points.append(v1)
        if d2 >= 0:
            clipped_points.append(v2)

        assert (
            len(clipped_points) > 0
        ), "At least one point should be inside the clipping plane. Otherwise, there is no intersection/collision."

        # If the points are on opposite sides, find the intersection point by linear interpolation
        if d1 * d2 < 0:
            assert (
                len(clipped_points) == 1
            ), "There should be exactly one point inside the clipping plane."
            t = d1 / (d1 - d2)
            intersection_point = v1 + (v2 - v1) * t
            clipped_points.append(intersection_point)

        assert (
            len(clipped_points) == 2
        ), "There should be exactly two points after clipping the incident edge."

        return tuple(clipped_points)

    def generate_contact(self, body_a: Body, body_b: Body) -> Optional[Contact]:
        """Checks for collision using the Separating Axis Theorem."""
        assert body_a.shape.get_type() == "polygon"
        assert body_b.shape.get_type() == "polygon"

        shape_a: PolygonShape = body_a.shape
        shape_b: PolygonShape = body_b.shape

        verts_a = shape_a.get_world_space_vertices(body_a.position, body_a.angle)
        verts_b = shape_b.get_world_space_vertices(body_b.position, body_b.angle)

        normals_a = shape_a.get_normals(body_a.position, body_a.angle)
        normals_b = shape_b.get_normals(body_b.position, body_b.angle)

        min_overlap = float("inf")
        collision_normal = None
        reference_shape_is_a = True
        reference_edge = None
        # the shape whose normal has the smallest overlap "owns" the collision normal
        # this corresponding edge of this normal is called "reference edge" and is defined
        #   as the edge that is being hit/penetrated
        # contrary the edge that penetrates the other shape is called "incident edge"
        #   and is defined as the edge on the other shape whose normal is most aligned
        #   (but pointing in the opposite direction) with the collision normal

        # find overlap, reference edge and collision normal
        for i_ab, (verts, normals) in enumerate(
            ((verts_a, normals_a), (verts_b, normals_b))
        ):
            for i in range(len(normals)):  # pylint: disable=consider-using-enumerate
                normal_i = normals[i]
                vert_i = verts[i]
                min_a_proj, max_a_proj = self._project_minmax(verts_a, normal_i)
                min_b_proj, max_b_proj = self._project_minmax(verts_b, normal_i)

                overlap = min(max_a_proj, max_b_proj) - max(min_a_proj, min_b_proj)
                if overlap <= 0:
                    return None  # Found a separating axis

                if overlap < min_overlap:
                    min_overlap = overlap
                    collision_normal = normal_i
                    reference_shape_is_a = i_ab == 0
                    reference_edge = (vert_i, verts[(i + 1) % len(verts)])

        # some synity checks
        assert (
            collision_normal is not None
        ), "Collision normal should be set if we reach here."
        assert (
            0 < min_overlap < float("inf")
        ), "Overlap should be a positive finite value."
        assert (
            reference_edge is not None
        ), "Reference edge should be set if we reach here."

        # find the incident edge on the other shape
        incident_shape_verts = verts_b
        incident_shape_normals = normals_b
        if not reference_shape_is_a:
            incident_shape_verts = verts_a
            incident_shape_normals = normals_a

        i_incident_normal = min(
            range(len(incident_shape_normals)),
            lambda i_normal: collision_normal.dot(incident_shape_normals[i_normal]),
        )
        incident_edge = (
            incident_shape_verts[i_incident_normal],
            incident_shape_verts[(i_incident_normal + 1) % len(incident_shape_verts)],
        )

        ### clip the incident edge against the perpendicular planes at the end of the reference edge
        # define the clipping plands: each of the planes is defined by a normal and an offset (how far the plane is moved away from the origin along its normal)
        reference_vertex_1, reference_vertex_2 = reference_edge
        clip_plane_1_normal = (reference_vertex_2 - reference_vertex_1).normalize()
        clip_plane_2_normal = (reference_vertex_1 - reference_vertex_2).normalize()
        clip_plane_1_offset = reference_vertex_1.dot(clip_plane_1_normal)
        clip_plane_2_offset = reference_vertex_2.dot(clip_plane_2_normal)

        # check wehther the incident edge corners are inside the clipping planes
        clipped_points = self._clip_incident_edge(
            incident_edge, clip_plane_1_normal, clip_plane_1_offset
        )
        clipped_points = self._clip_incident_edge(
            clipped_points, clip_plane_2_normal, clip_plane_2_offset
        )

        return Contact(body_a, body_b, collision_normal, min_overlap, list(clipped_points))


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

            # if self.debug_drawer:
            #     # draw line from circle center to closest point on edge in blue
            #     self.debug_drawer.draw_line(
            #         body_a.position, closest_on_edge, color=(0, 0, 255)
            #     )

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

        # TODO add collision point
        return Contact(body_a, body_b, normal, penetration)
